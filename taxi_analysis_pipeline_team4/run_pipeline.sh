#!/usr/bin/env bash
# NYC Yellow Taxi 분석 전체 실행기
# 다운로드/로딩 비교 → 전처리 → 통계 → 시각화 → 모델링 → 리포트 순으로 실행한다.
set -euo pipefail
trap 'echo "오류: ${LINENO}번째 줄에서 파이프라인이 중단되었습니다." >&2' ERR

PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${PIPELINE_DIR}/.." && pwd)"
if [[ -x "${PROJECT_DIR}/taxi/bin/python" ]]; then
  DEFAULT_PYTHON="${PROJECT_DIR}/taxi/bin/python"
else
  DEFAULT_PYTHON="python3"
fi
PYTHON_BIN="${PYTHON_BIN:-${DEFAULT_PYTHON}}"
export MPLCONFIGDIR="${PIPELINE_DIR}/.matplotlib"
mkdir -p "${MPLCONFIGDIR}"

cd "${PROJECT_DIR}"
mkdir -p "${PIPELINE_DIR}/outputs"

echo "[1/6] 원본 다운로드 및 Pandas/Polars 로딩 비교"
if [[ "${FORCE_DOWNLOAD:-0}" == "1" ]]; then
  "${PYTHON_BIN}" "${PIPELINE_DIR}/src/data_loader.py" --force-download
else
  "${PYTHON_BIN}" "${PIPELINE_DIR}/src/data_loader.py"
fi

echo "[2/6] 원본 데이터 전처리"
"${PYTHON_BIN}" "${PIPELINE_DIR}/src/data_preprocessing.py"

echo "[3/6] 통계 분석"
"${PYTHON_BIN}" "${PIPELINE_DIR}/src/statistical_analysis.py" | tee "${PIPELINE_DIR}/outputs/statistics.txt"

echo "[4/6] 원본 데이터 및 전처리 후 데이터 시각화"
"${PYTHON_BIN}" "${PIPELINE_DIR}/src/notebook_runner.py"

echo "[5/6] 모델링"
"${PYTHON_BIN}" -c "from taxi_analysis_pipeline.src.modeling import main; main()"

echo "[6/6] Jinja2 HTML 리포트"
"${PYTHON_BIN}" "${PIPELINE_DIR}/src/report.py"

echo "완료: ${PIPELINE_DIR}/outputs/report.html"
