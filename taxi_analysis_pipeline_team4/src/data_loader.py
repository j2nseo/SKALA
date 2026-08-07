"""공식 TLC 링크에서 원본 데이터를 받고 Pandas/Polars 로딩을 비교한다.

원본 Parquet가 없으면 자동으로 다운로드하며, ``--force-download``를 지정하면 기존
파일을 새로 받는다. 같은 파일을 Pandas와 Polars로 각각 읽어 시간과 핵심 결과를
검증하고, 터미널 및 ``outputs/data_loading_comparison.json``에 기록한다.
"""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import polars as pl


SRC_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SRC_DIR.parent
PROJECT_DIR = PIPELINE_DIR.parent
OUTPUT_DIR = PIPELINE_DIR / "outputs"
DATA_URL = (
    "https://d37ci6vzurychx.cloudfront.net/trip-data/"
    "yellow_tripdata_2026-05.parquet"
)
RAW_DATA_PATH = PROJECT_DIR / "yellow_tripdata_2026-05.parquet"
COMPARISON_PATH = OUTPUT_DIR / "data_loading_comparison.json"
CHECKSUM_COLUMN = "total_amount"
TIME_COLUMN = "tpep_pickup_datetime"


def human_bytes(size: int) -> str:
    """바이트 크기를 사람이 읽기 쉬운 단위로 표현한다."""
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def download_file(url: str, destination: Path, force: bool = False) -> bool:
    """HTTP 응답을 임시 파일에 스트리밍한 뒤 성공 시 원자적으로 교체한다."""
    if destination.is_file() and destination.stat().st_size > 0 and not force:
        print(f"[데이터] 기존 원본 사용: {destination} ({human_bytes(destination.stat().st_size)})")
        return False

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".download")
    request = Request(url, headers={"User-Agent": "taxi-analysis-pipeline/1.0"})
    print(f"[데이터] 다운로드 시작: {url}")
    try:
        with urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            status = getattr(response, "status", 200)
            if status != 200:
                raise RuntimeError(f"다운로드 서버가 HTTP {status}를 반환했습니다.")
            expected = int(response.headers.get("Content-Length", 0))
            received = 0
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                received += len(chunk)
            if expected and received != expected:
                raise RuntimeError(
                    f"다운로드 크기가 일치하지 않습니다: 예상 {expected}, 실제 {received}"
                )
        if temporary.stat().st_size == 0:
            raise RuntimeError("다운로드한 파일이 비어 있습니다.")
        os.replace(temporary, destination)
    except (HTTPError, URLError, TimeoutError, OSError, RuntimeError) as exc:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"원본 데이터 다운로드에 실패했습니다: {url}") from exc

    print(f"[데이터] 다운로드 완료: {destination} ({human_bytes(destination.stat().st_size)})")
    return True


def validate_columns(columns: list[str]) -> None:
    """두 로더의 비교에 사용할 핵심 컬럼이 존재하는지 확인한다."""
    required = {CHECKSUM_COLUMN, TIME_COLUMN}
    missing = sorted(required - set(columns))
    if missing:
        raise ValueError(f"원본 데이터에 비교용 필수 컬럼이 없습니다: {missing}")


def load_with_pandas(path: Path) -> tuple[pd.DataFrame, dict]:
    """Pandas로 전체 Parquet를 읽고 측정값을 반환한다."""
    started = time.perf_counter()
    try:
        frame = pd.read_parquet(path)
    except Exception as exc:
        raise RuntimeError(f"Pandas Parquet 로딩에 실패했습니다: {path}") from exc
    elapsed = time.perf_counter() - started
    validate_columns(list(frame.columns))
    result = {
        "version": pd.__version__,
        "seconds": round(elapsed, 4),
        "rows": int(len(frame)),
        "columns": int(frame.shape[1]),
        "column_names": list(frame.columns),
        "total_amount_sum": round(float(frame[CHECKSUM_COLUMN].sum()), 6),
        "pickup_min": frame[TIME_COLUMN].min().isoformat(),
        "pickup_max": frame[TIME_COLUMN].max().isoformat(),
        "memory_mb": round(float(frame.memory_usage(deep=True).sum() / 1024**2), 2),
    }
    return frame, result


def load_with_polars(path: Path) -> tuple[pl.DataFrame, dict]:
    """Polars로 전체 Parquet를 읽고 Pandas와 동일한 측정값을 반환한다."""
    started = time.perf_counter()
    try:
        frame = pl.read_parquet(path)
    except Exception as exc:
        raise RuntimeError(f"Polars Parquet 로딩에 실패했습니다: {path}") from exc
    elapsed = time.perf_counter() - started
    validate_columns(frame.columns)
    total = frame.select(pl.col(CHECKSUM_COLUMN).sum()).item()
    pickup = frame.select(
        pl.col(TIME_COLUMN).min().alias("minimum"),
        pl.col(TIME_COLUMN).max().alias("maximum"),
    ).row(0, named=True)
    result = {
        "version": pl.__version__,
        "seconds": round(elapsed, 4),
        "rows": int(frame.height),
        "columns": int(frame.width),
        "column_names": frame.columns,
        "total_amount_sum": round(float(total), 6),
        "pickup_min": pickup["minimum"].isoformat(),
        "pickup_max": pickup["maximum"].isoformat(),
        "memory_mb": round(float(frame.estimated_size("mb")), 2),
    }
    return frame, result


def compare_results(pandas_result: dict, polars_result: dict) -> dict:
    """크기·컬럼·핵심 합계·기간을 비교해 두 로딩 결과의 동등성을 판단한다."""
    pandas_seconds = pandas_result["seconds"]
    polars_seconds = polars_result["seconds"]
    faster = "Pandas" if pandas_seconds < polars_seconds else "Polars"
    slower_seconds = max(pandas_seconds, polars_seconds)
    faster_seconds = min(pandas_seconds, polars_seconds)
    comparison = {
        "rows_match": pandas_result["rows"] == polars_result["rows"],
        "columns_match": pandas_result["columns"] == polars_result["columns"],
        "column_names_match": pandas_result["column_names"] == polars_result["column_names"],
        "total_amount_sum_match": bool(np.isclose(
            pandas_result["total_amount_sum"],
            polars_result["total_amount_sum"],
            rtol=1e-9,
            atol=1e-6,
        )),
        "pickup_range_match": (
            pandas_result["pickup_min"] == polars_result["pickup_min"]
            and pandas_result["pickup_max"] == polars_result["pickup_max"]
        ),
        "faster_library": faster,
        "speedup": round(slower_seconds / faster_seconds, 2) if faster_seconds else None,
    }
    comparison["all_results_match"] = all(
        comparison[key]
        for key in (
            "rows_match", "columns_match", "column_names_match",
            "total_amount_sum_match", "pickup_range_match",
        )
    )
    return comparison


def print_comparison(payload: dict) -> None:
    """비교 결과를 터미널에서 빠르게 읽을 수 있는 표로 출력한다."""
    pandas_result = payload["pandas"]
    polars_result = payload["polars"]
    comparison = payload["comparison"]
    print("\n" + "=" * 78)
    print("Pandas vs Polars 원본 Parquet 로딩 비교")
    print("=" * 78)
    print(f"{'항목':<22}{'Pandas':>22}{'Polars':>22}")
    print(f"{'버전':<22}{pandas_result['version']:>22}{polars_result['version']:>22}")
    print(f"{'로딩 시간(초)':<22}{pandas_result['seconds']:>22.4f}{polars_result['seconds']:>22.4f}")
    print(f"{'행 수':<22}{pandas_result['rows']:>22,}{polars_result['rows']:>22,}")
    print(f"{'열 수':<22}{pandas_result['columns']:>22}{polars_result['columns']:>22}")
    print(f"{'메모리 추정(MB)':<22}{pandas_result['memory_mb']:>22.2f}{polars_result['memory_mb']:>22.2f}")
    verdict = "일치" if comparison["all_results_match"] else "불일치"
    print(f"\n결과 검증: {verdict}")
    print(
        f"속도: {comparison['faster_library']}가 "
        f"약 {comparison['speedup']:.2f}배 빠름"
    )


def parse_args() -> argparse.Namespace:
    """강제 재다운로드 옵션을 해석한다."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="기존 원본 파일이 있어도 공식 링크에서 다시 다운로드합니다.",
    )
    return parser.parse_args()


def main() -> None:
    """다운로드, 양쪽 로딩, 결과 검증과 JSON 저장을 순서대로 실행한다."""
    args = parse_args()
    downloaded = download_file(DATA_URL, RAW_DATA_PATH, force=args.force_download)
    pandas_frame, pandas_result = load_with_pandas(RAW_DATA_PATH)
    if pandas_frame.empty:
        raise ValueError("Pandas 로딩 결과가 비어 있습니다.")
    del pandas_frame
    gc.collect()
    polars_frame, polars_result = load_with_polars(RAW_DATA_PATH)
    if polars_frame.is_empty():
        raise ValueError("Polars 로딩 결과가 비어 있습니다.")
    del polars_frame
    gc.collect()

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_url": DATA_URL,
        "local_path": str(RAW_DATA_PATH),
        "file_size_bytes": RAW_DATA_PATH.stat().st_size,
        "downloaded_this_run": downloaded,
        "pandas": pandas_result,
        "polars": polars_result,
        "comparison": compare_results(pandas_result, polars_result),
    }
    print_comparison(payload)
    if not payload["comparison"]["all_results_match"]:
        raise ValueError("Pandas와 Polars의 핵심 로딩 결과가 일치하지 않습니다.")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    COMPARISON_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"비교 결과 저장: {COMPARISON_PATH}")


if __name__ == "__main__":
    main()
