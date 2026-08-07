"""분석 산출물을 Jinja2 기반 HTML 리포트로 조립한다.

데이터 로딩 비교, 모델 평가지표와 변수 중요도, 요금제별 오차 및 두 시각화
노트북에서 저장한 차트를 읽는다. 분석이나 모델 학습은 다시 수행하지 않고
outputs/report.html만 생성하므로, 전체 파이프라인 완료 후 단독 재실행할 수 있다.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape


SRC_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SRC_DIR.parent
OUTPUT_DIR = PIPELINE_DIR / "outputs"
TEMPLATE_DIR = PIPELINE_DIR / "templates"


def load_csv_records(path: Path) -> list[dict]:
    """선택 산출물이 없으면 빈 표를, 손상됐다면 명확한 오류를 반환한다."""
    if not path.exists():
        return []
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        raise RuntimeError(f"리포트용 CSV를 읽지 못했습니다: {path}") from exc
    unnamed = [column for column in frame.columns if column.startswith("Unnamed:")]
    return frame.drop(columns=unnamed).to_dict("records")


def load_json(path: Path, label: str) -> dict:
    """필수 JSON 산출물을 읽고 객체 형식인지 검증한다."""
    if not path.is_file():
        raise FileNotFoundError(f"{label} 파일이 없습니다: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{label} JSON을 읽지 못했습니다: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{label} JSON의 최상위 값은 객체여야 합니다: {path}")
    return payload


def main() -> None:
    """저장된 분석 산출물을 검증하고 최종 HTML을 생성한다."""
    if not OUTPUT_DIR.is_dir():
        raise FileNotFoundError(f"산출물 폴더가 없습니다: {OUTPUT_DIR}")
    metrics_path = OUTPUT_DIR / "metrics.json"
    metrics = load_json(metrics_path, "모델 평가지표")
    required_metrics = {"train_rows", "test_rows", "n_features", "best_trees", "baseline", "model"}
    missing = sorted(required_metrics - set(metrics))
    if missing:
        raise ValueError(f"metrics.json에 필수 항목이 없습니다: {missing}")
    loading = load_json(OUTPUT_DIR / "data_loading_comparison.json", "데이터 로딩 비교")
    if not loading.get("comparison", {}).get("all_results_match", False):
        raise ValueError("Pandas와 Polars 로딩 결과 검증이 완료되지 않았습니다.")
    visualizations = sorted(
        path.name for path in OUTPUT_DIR.iterdir()
        if path.name.startswith(("visualization_raw_", "visualization_processed_"))
        and path.suffix.lower() in {".png", ".html"}
    )
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )
    try:
        template = env.get_template("report.html.j2")
    except Exception as exc:
        raise RuntimeError(f"Jinja2 템플릿을 읽지 못했습니다: {TEMPLATE_DIR}") from exc
    html = template.render(
        title="NYC Yellow Taxi 요금 예측 분석 리포트",
        generated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        metrics=metrics,
        loading=loading,
        importance=load_csv_records(OUTPUT_DIR / "feature_importance.csv")[:15],
        errors=load_csv_records(OUTPUT_DIR / "error_by_ratecode.csv"),
        visualizations=visualizations,
        artifacts=sorted(path.name for path in OUTPUT_DIR.iterdir()),
    )
    output_path = OUTPUT_DIR / "report.html"
    try:
        output_path.write_text(html, encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"HTML 리포트를 저장하지 못했습니다: {output_path}") from exc
    print(f"HTML 리포트 생성: {output_path}")


if __name__ == "__main__":
    main()
