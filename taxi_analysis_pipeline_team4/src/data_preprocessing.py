"""NYC Yellow Taxi 원본 Parquet를 학습 가능한 CSV로 전처리한다.

2026년 5월 원본 데이터를 날짜 기준 train(1~20일)과 test(21~31일)로 나누고,
결측치·불가능한 값·RatecodeID별 IQR 이상치를 처리한다. 요금 예측 시점에 알 수
없는 누수 컬럼을 제거한 뒤 결과를 ``data/processed``에 저장한다.

입력  : 프로젝트 루트/yellow_tripdata_2026-05.parquet
출력  : taxi_analysis_pipeline/data/processed/clean_{train,test}[_with_ids].csv
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


SRC_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SRC_DIR.parent
PROJECT_DIR = PIPELINE_DIR.parent
RAW_DATA_PATH = PROJECT_DIR / "yellow_tripdata_2026-05.parquet"
PROCESSED_DIR = PIPELINE_DIR / "data" / "processed"

PICKUP_COLUMN = "tpep_pickup_datetime"
DROPOFF_COLUMN = "tpep_dropoff_datetime"
TARGET = "fare_ex_tip"
TRAIN_END_DAY = 20
IQR_K = 1.5
IQR_K_OVERRIDE = {1.0: 3.0}

REQUIRED_COLUMNS = {
    PICKUP_COLUMN, DROPOFF_COLUMN, "trip_distance", "RatecodeID",
    "passenger_count", "store_and_fwd_flag", "total_amount", "tip_amount",
    "VendorID", "PULocationID", "DOLocationID",
}

LEAKAGE_COLUMNS = [
    DROPOFF_COLUMN, "payment_type", "trip_duration_min", "speed_mph",
    "fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount",
    "improvement_surcharge", "total_amount", "congestion_surcharge",
    "Airport_fee", "cbd_congestion_fee",
]
ID_COLUMNS = ["VendorID", "PULocationID", "DOLocationID"]


def log(message: str) -> None:
    """전처리 진행 상황을 즉시 출력한다."""
    print(f"[전처리] {message}", flush=True)


def validate_columns(frame: pd.DataFrame) -> None:
    """후속 전처리와 모델링에 반드시 필요한 컬럼을 확인한다."""
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise ValueError(f"원본 데이터에 필수 컬럼이 없습니다: {missing}")


def load_raw_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """Parquet를 읽고 날짜 컬럼을 안전하게 datetime으로 변환한다."""
    if not path.is_file():
        raise FileNotFoundError(
            f"원본 데이터가 없습니다: {path}\n"
            "yellow_tripdata_2026-05.parquet를 프로젝트 루트에 두세요."
        )
    try:
        frame = pd.read_parquet(path)
    except Exception as exc:
        raise RuntimeError(f"Parquet 로딩에 실패했습니다: {path}") from exc

    if frame.empty:
        raise ValueError("원본 데이터가 비어 있습니다.")
    validate_columns(frame)
    for column in (PICKUP_COLUMN, DROPOFF_COLUMN):
        frame[column] = pd.to_datetime(frame[column], errors="coerce")
    invalid_dates = frame[[PICKUP_COLUMN, DROPOFF_COLUMN]].isna().any(axis=1)
    if invalid_dates.any():
        log(f"날짜 변환 실패 {int(invalid_dates.sum()):,}행 제거")
        frame = frame.loc[~invalid_dates].copy()
    return frame


def split_by_date(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """2026년 5월만 남기고 시간 순서에 맞춰 train/test를 분리한다."""
    may = frame.loc[
        frame[PICKUP_COLUMN].ge("2026-05-01")
        & frame[PICKUP_COLUMN].lt("2026-06-01")
    ].copy()
    if may.empty:
        raise ValueError("2026년 5월 승차 데이터가 없습니다.")
    day = may[PICKUP_COLUMN].dt.day
    train = may.loc[day.le(TRAIN_END_DAY)].copy()
    test = may.loc[day.gt(TRAIN_END_DAY)].copy()
    if train.empty or test.empty:
        raise ValueError("날짜 분리 후 train 또는 test 데이터가 비었습니다.")
    return train, test


def fix_ratecode(frame: pd.DataFrame) -> pd.DataFrame:
    """오류 코드는 제거하고 flex fare의 결측 RatecodeID는 0으로 보존한다."""
    cleaned = frame.loc[~frame["RatecodeID"].isin([99.0, 6.0])].copy()
    cleaned["RatecodeID"] = cleaned["RatecodeID"].fillna(0.0)
    return cleaned


def clean_common(frame: pd.DataFrame, passenger_mode: float) -> pd.DataFrame:
    """train에서 정한 규칙을 train/test에 동일하게 적용한다."""
    cleaned = fix_ratecode(frame)
    cleaned = cleaned.loc[cleaned["store_and_fwd_flag"] != "Y"].copy()
    cleaned = cleaned.drop(columns=["store_and_fwd_flag"])
    invalid_passenger = cleaned["passenger_count"].isna() | cleaned["passenger_count"].eq(0)
    cleaned.loc[invalid_passenger, "passenger_count"] = passenger_mode
    cleaned = cleaned.loc[cleaned["passenger_count"].le(5)].copy()
    cleaned = cleaned.loc[cleaned["trip_distance"].gt(0)].copy()
    cleaned["trip_duration_min"] = (
        cleaned[DROPOFF_COLUMN] - cleaned[PICKUP_COLUMN]
    ).dt.total_seconds().div(60)
    cleaned = cleaned.loc[cleaned["trip_duration_min"].gt(0)].copy()
    cleaned["speed_mph"] = cleaned["trip_distance"].div(
        cleaned["trip_duration_min"].div(60)
    )
    return cleaned


def iqr_upper(series: pd.Series, k: float) -> float:
    """유한한 값으로 Tukey IQR 상한을 계산한다."""
    values = series.replace([np.inf, -np.inf], np.nan).dropna()
    if values.empty:
        raise ValueError(f"IQR 경계를 계산할 유효값이 없습니다: {series.name}")
    q1, q3 = values.quantile([0.25, 0.75])
    return float(q3 + k * (q3 - q1))


def build_bounds(train: pd.DataFrame) -> pd.DataFrame:
    """데이터 누수를 막기 위해 train만으로 RatecodeID별 상한을 학습한다."""
    records = []
    for ratecode, group in train.groupby("RatecodeID"):
        k = IQR_K_OVERRIDE.get(ratecode, IQR_K)
        records.append({
            "RatecodeID": ratecode,
            "dist_upper": iqr_upper(group["trip_distance"], k),
            "dur_upper": iqr_upper(group["trip_duration_min"], k),
            "speed_upper": iqr_upper(group["speed_mph"], k),
        })
    if not records:
        raise ValueError("RatecodeID별 IQR 경계를 생성하지 못했습니다.")
    return pd.DataFrame(records).set_index("RatecodeID")


def apply_bounds(frame: pd.DataFrame, bounds: pd.DataFrame) -> pd.DataFrame:
    """train 경계가 있는 요금제만 남기고 거리·시간·속도 이상치를 제거한다."""
    merged = frame.merge(bounds, left_on="RatecodeID", right_index=True, how="left")
    unknown = merged["dist_upper"].isna()
    if unknown.any():
        log(f"train에 없던 RatecodeID {int(unknown.sum()):,}행 제거")
    keep = (
        merged["trip_distance"].le(merged["dist_upper"])
        & merged["trip_duration_min"].le(merged["dur_upper"])
        & merged["speed_mph"].le(merged["speed_upper"])
    )
    return merged.loc[keep].drop(columns=["dist_upper", "dur_upper", "speed_upper"])


def add_target(frame: pd.DataFrame) -> pd.DataFrame:
    """팁을 제외한 결제금액을 타깃으로 만들고 비정상 결제를 제거한다."""
    result = frame.copy()
    result[TARGET] = result["total_amount"] - result["tip_amount"]
    return result.loc[result[TARGET].gt(0)].copy()


def save_outputs(train: pd.DataFrame, test: pd.DataFrame) -> None:
    """누수 컬럼을 제거한 두 가지 버전을 UTF-8 CSV로 저장한다."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    leakage = [column for column in LEAKAGE_COLUMNS if column in train.columns]
    without_ids = leakage + [column for column in ID_COLUMNS if column in train.columns]
    outputs = {
        "clean_train.csv": train.drop(columns=without_ids),
        "clean_test.csv": test.drop(columns=without_ids),
        "clean_train_with_ids.csv": train.drop(columns=leakage),
        "clean_test_with_ids.csv": test.drop(columns=leakage),
    }
    for filename, frame in outputs.items():
        path = PROCESSED_DIR / filename
        frame.to_csv(path, index=False)
        log(f"저장: {path} ({len(frame):,}행 × {frame.shape[1]}열)")


def main() -> None:
    """원본 로드부터 CSV 저장까지 전체 전처리 단계를 실행한다."""
    raw = load_raw_data()
    train_raw, test_raw = split_by_date(raw)
    valid_counts = train_raw.loc[train_raw["passenger_count"].gt(0), "passenger_count"].mode()
    if valid_counts.empty:
        raise ValueError("passenger_count 최빈값을 계산할 유효한 train 행이 없습니다.")
    passenger_mode = float(valid_counts.iloc[0])

    train = clean_common(train_raw, passenger_mode)
    test = clean_common(test_raw, passenger_mode)
    bounds = build_bounds(train)
    train = add_target(apply_bounds(train, bounds))
    test = add_target(apply_bounds(test, bounds))
    if train.empty or test.empty:
        raise ValueError("전처리 완료 후 train 또는 test 데이터가 비었습니다.")

    save_outputs(train, test)
    log(f"완료: passenger_count 대체값={passenger_mode:g}")
    log(f"최종 train={train.shape}, test={test.shape}")


if __name__ == "__main__":
    main()
