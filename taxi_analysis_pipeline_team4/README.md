# NYC Yellow Taxi 분석 파이프라인

NYC Yellow Taxi 원본 데이터 진단부터 전처리 후 분석, 요금 예측 모델 학습,
HTML 리포트 생성까지 한 번에 실행하는 프로젝트입니다. 통계·시각화·모델링의
역할을 분리해 각 단계가 무엇을 담당하는지 명확하게 구성했습니다.
별도로 데이터 파일을 전달받을 필요 없이 공식 TLC 링크에서 원본 Parquet를
자동 다운로드하는 단계부터 시작합니다.

## 폴더 구조

```text
taxi_analysis_pipeline/
├── notebooks/
│   ├── visualization_raw.ipynb        # 전처리 전 원본 데이터 EDA
│   └── visualization_processed.ipynb  # 전처리 완료 데이터 EDA
├── data/
│   └── processed/                     # 전처리 스크립트가 생성한 CSV
├── src/
│   ├── data_loader.py                 # 공식 데이터 다운로드와 Pandas/Polars 비교
│   ├── data_preprocessing.py          # 원본 정제와 시간 기준 train/test 분리
│   ├── statistical_analysis.py        # 가설 검정과 효과크기 계산
│   ├── notebook_runner.py             # 두 노트북 자동 실행 및 차트 저장
│   ├── modeling.py                    # 피처 엔지니어링과 XGBoost 모델 학습
│   └── report.py                      # Jinja2 HTML 리포트 생성
├── templates/
│   └── report.html.j2                 # HTML 리포트 템플릿
├── outputs/                           # 모델, 지표, 차트와 리포트 산출물
├── requirements.txt                   # 추가 Python 의존성
└── run_pipeline.sh                    # 전체 파이프라인 실행기
```

## 원본 데이터

파이프라인이 다음 NYC TLC 공식 링크에서 원본을 자동으로 다운로드합니다.

[yellow_tripdata_2026-05.parquet 내려받기](https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2026-05.parquet)

첫 실행에서는 프로젝트 루트에 원본을 저장합니다. 이후 실행은 이미 받은 파일을
재사용해 불필요한 네트워크 전송을 막습니다.

## 실행 방법

프로젝트 루트에서 다음 명령을 실행합니다.

```bash
./taxi_analysis_pipeline/run_pipeline.sh
```

스크립트는 다음 순서로 진행됩니다.

1. 공식 원본 다운로드 및 Pandas/Polars 로딩 비교
2. 원본 Parquet 전처리 및 train/test 생성
3. 전처리 완료 데이터 통계 분석
4. 원본 데이터와 전처리 후 데이터 시각화
5. XGBoost 요금 예측 모델 학습 및 평가
6. Jinja2 HTML 리포트 생성

현재 모델링은 85% 구간에서 최적 트리 수를 찾은 뒤 전체 학습 데이터로 처음부터
재학습합니다. 전체 데이터 실행은 환경에 따라 30분 이상 걸릴 수 있습니다.

## 개별 단계 실행

프로젝트에 포함된 가상환경을 사용하는 경우:

```bash
taxi/bin/python taxi_analysis_pipeline/src/data_loader.py
taxi/bin/python taxi_analysis_pipeline/src/data_preprocessing.py
taxi/bin/python taxi_analysis_pipeline/src/statistical_analysis.py
taxi/bin/python taxi_analysis_pipeline/src/notebook_runner.py
taxi/bin/python -c "from taxi_analysis_pipeline.src.modeling import main; main()"
taxi/bin/python taxi_analysis_pipeline/src/report.py
```

리포트만 다시 만들 때는 모델을 재학습할 필요 없이 마지막 명령만 실행하면 됩니다.

## 주요 산출물

전처리 CSV는 `taxi_analysis_pipeline/data/processed/`, 분석 결과는
`taxi_analysis_pipeline/outputs/`에 저장됩니다.

| 전처리 산출물 | 설명 |
|---|---|
| `clean_train_with_ids.csv` | 통계·시각화·모델 학습용 1~20일 데이터 |
| `clean_test_with_ids.csv` | 모델 평가용 21~31일 데이터 |
| `clean_train.csv`, `clean_test.csv` | 위치·업체 ID를 제외한 보조 버전 |

| 산출물 | 설명 |
|---|---|
| `data_loading_comparison.json` | Pandas/Polars 속도 및 결과 비교 |
| `statistics.txt` | 통계 분석 콘솔 결과 |
| `visualization_raw_*.png/html` | 원본 데이터 차트 |
| `visualization_processed_*.png/html` | 전처리 완료 데이터 차트 |
| `fare_model_pipeline.joblib` | 전처리와 XGBoost가 결합된 학습 모델 |
| `metrics.json` | 베이스라인 및 최종 모델 평가지표 |
| `feature_importance.csv` | 변수 중요도 |
| `error_by_ratecode.csv` | 요금제별 오차 분석 |
| `test_predictions.csv.gz` | 테스트 실제값과 예측값 |
| `report.html` | 최종 자동 생성 리포트 |

최종 결과는 브라우저에서 [outputs/report.html](outputs/report.html)을 열어 확인할 수 있습니다.

## 환경 설정

필요한 추가 패키지는 다음 명령으로 설치합니다.

```bash
pip install -r taxi_analysis_pipeline/requirements.txt
```

macOS에서는 `AppleGothic`, Linux에서는 `NanumGothic`을 자동 탐색해 Matplotlib에
적용합니다. Linux에 나눔고딕이 없다면 운영체제 패키지 관리자로 별도 설치해야 합니다.
