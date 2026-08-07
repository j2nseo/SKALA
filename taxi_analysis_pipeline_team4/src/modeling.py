"""NYC Yellow Taxi 요금 예측 모델링 파이프라인.
================================================================================
데이터 : data/processed/clean_train_with_ids.csv / clean_test_with_ids.csv
목표   : 승차 시각과 이동 거리로 팁 제외 결제금액(fare_ex_tip)을 예측한다.

실행   : README의 모듈 import 명령 또는 run_pipeline.sh 사용

정제된 train/test 데이터로 sklearn Pipeline을 학습하고 모델 및 평가 산출물을
저장한다. 통계, EDA, 시각화, 결측/이상치 정제, 리포트 생성은 다루지 않는다.

핵심 설계
  - 시간순 분할을 끝까지 유지한다. 미래 데이터로 과거를 예측하는 누수를 막기 위함이다.
  - 타깃 인코딩은 K-Fold OOF 로 계산해 자기 정답이 자기 피처로 새어드는 것을 막는다.
  - 손실함수는 L1(reg:absoluteerror)을 쓴다. 평가 지표가 MAE 이므로 직접 최적화한다.
  - 트리 수는 조기 종료로 결정한 뒤, train 100% 로 다시 학습해 데이터를 버리지 않는다.
================================================================================
"""

from __future__ import annotations

import json
import time
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.model_selection import KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════════════════════════
# 설정 - 인자 없이 실행하기 위해 상수로 고정한다
# ══════════════════════════════════════════════════════════════════════════════
SRC_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = SRC_DIR.parent
PROJECT_DIR = PIPELINE_DIR.parent
PROCESSED_DIR = PIPELINE_DIR / "data" / "processed"
TRAIN_PATH = PROCESSED_DIR / "clean_train_with_ids.csv"
TEST_PATH = PROCESSED_DIR / "clean_test_with_ids.csv"
OUTPUT_DIR = PIPELINE_DIR / "outputs"

TARGET = "fare_ex_tip"                      # 종속변수: 팁 제외 결제금액
TIME_COLUMN = "tpep_pickup_datetime"        # 승차 시각
SEED = 42

# 빠른 점검용. 0 이면 전체 데이터를 쓴다.
# 전체 실행은 약 15분, SAMPLE_ROWS=300_000 이면 약 2분 소요된다.
SAMPLE_ROWS = 0

VALIDATION_RATIO = 0.15                     # train 마지막 15% 를 조기 종료 판정에 쓴다
MAX_ESTIMATORS = 4000                       # 조기 종료 상한 (실험상 약 3,986 에서 수렴)
EARLY_STOPPING_ROUNDS = 75
TE_FOLDS = 5                                # 타깃 인코딩 K-Fold 수
TE_SMOOTHING = 20.0                         # 표본이 적은 그룹을 전체 평균 쪽으로 당기는 정도

AIRPORT_ZONES = [1, 132, 138]               # Newark, JFK, LaGuardia 의 TLC 존 ID

# 요금제 코드 이름표. 0번은 전처리 단계에서 우리가 신설한 flex fare 카테고리다.
RATECODE_LABELS = {
    0: "flex fare", 1: "일반", 2: "JFK 정액",
    3: "Newark", 4: "Nassau/Westchester", 5: "협상요금",
}


def log(message: str) -> None:
    """진행 상황을 시각과 함께 출력한다."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def load_data(path: Path) -> pd.DataFrame:
    """정제 완료된 CSV를 읽어 시간순 모델링 입력으로 만든다."""
    if not path.is_file():
        raise FileNotFoundError(
            f"전처리 데이터가 없습니다: {path}\n"
            "src/data_preprocessing.py를 먼저 실행하세요."
        )
    try:
        data = pd.read_csv(path, parse_dates=[TIME_COLUMN])
    except Exception as exc:
        raise RuntimeError(f"모델링 데이터 로딩에 실패했습니다: {path}") from exc
    required = {
        TIME_COLUMN, TARGET, "trip_distance", "passenger_count", "RatecodeID",
        "VendorID", "PULocationID", "DOLocationID",
    }
    missing = sorted(required - set(data.columns))
    if missing:
        raise ValueError(f"모델링 데이터에 필수 컬럼이 없습니다: {missing}")
    if data.empty:
        raise ValueError(f"모델링 데이터가 비어 있습니다: {path}")
    return data.sort_values(TIME_COLUMN).reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# 4. ML Pipeline - 전처리 단계를 sklearn Transformer 로 구현한다
# ══════════════════════════════════════════════════════════════════════════════
class FeatureBuilder(BaseEstimator, TransformerMixin):
    """행 단위로 독립 계산되는 파생변수를 만든다.

    다른 행의 정보를 쓰지 않으므로 train/test 구분 없이 동일하게 적용된다.
    따라서 fit 에서 학습할 것이 없다.
    """

    # 순환 인코딩과 플래그, 공간 파생변수 목록
    CYCLIC = ["hour_sin", "hour_cos", "weekday_sin", "weekday_cos"]
    FLAGS = ["is_weekend", "is_rush_hour", "is_overnight",
             "same_zone", "pickup_airport", "dropoff_airport"]
    RAW = ["trip_distance", "passenger_count", "RatecodeID",
           "VendorID", "PULocationID", "DOLocationID"]

    def fit(self, X, y=None):
        """행 단위 피처는 학습할 상태가 없으므로 입력 객체만 검증한다."""
        if not isinstance(X, pd.DataFrame):
            raise TypeError("FeatureBuilder 입력은 pandas DataFrame이어야 합니다.")
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """원본 입력에서 시간·공간·운행 특성 및 인코딩 키를 생성한다."""
        pickup = X[TIME_COLUMN]
        # 분·초까지 반영한 연속 시각. 정시 경계에서 값이 뚝 끊기지 않는다.
        hour = pickup.dt.hour + pickup.dt.minute / 60 + pickup.dt.second / 3600
        weekday = pickup.dt.dayofweek
        pu = X["PULocationID"].astype("int32")
        do = X["DOLocationID"].astype("int32")

        f = pd.DataFrame(index=X.index)
        f["trip_distance"] = X["trip_distance"].astype("float32")
        f["passenger_count"] = X["passenger_count"].astype("float32")
        f["RatecodeID"] = X["RatecodeID"].astype("int16")

        # 자정(23시->0시)과 주말 경계가 자연스럽게 이어지도록 sin/cos 로 변환한다
        f["hour_sin"] = np.sin(2 * np.pi * hour / 24).astype("float32")
        f["hour_cos"] = np.cos(2 * np.pi * hour / 24).astype("float32")
        f["weekday_sin"] = np.sin(2 * np.pi * weekday / 7).astype("float32")
        f["weekday_cos"] = np.cos(2 * np.pi * weekday / 7).astype("float32")

        f["is_weekend"] = weekday.ge(5).astype("int8")
        f["is_rush_hour"] = (weekday.lt(5)
                             & (pickup.dt.hour.between(7, 9)
                                | pickup.dt.hour.between(16, 19))).astype("int8")
        f["is_overnight"] = pickup.dt.hour.between(0, 5).astype("int8")

        # 존 ID 는 숫자 크기에 의미가 없으므로 범주형으로 넘긴다
        f["VendorID"] = X["VendorID"].astype("int32")
        f["PULocationID"] = pu
        f["DOLocationID"] = do

        f["same_zone"] = pu.eq(do).astype("int8")
        f["pickup_airport"] = pu.isin(AIRPORT_ZONES).astype("int8")
        f["dropoff_airport"] = do.isin(AIRPORT_ZONES).astype("int8")

        # 통계 인코딩 단계에서 쓸 그룹 키. 마지막에 제거한다.
        f["_route"] = pu.astype("int64") * 1000 + do.astype("int64")
        f["_tow"] = (weekday * 24 + pickup.dt.hour).astype("int64")   # 요일x시간 168단계
        f["_rc"] = X["RatecodeID"].astype("int64")
        f["_rc_route"] = f["_rc"] * 10 ** 7 + f["_route"]
        f["_rc_tow"] = f["_rc"] * 1000 + f["_tow"]
        f["_pickup_tow"] = pu.astype("int64") * 200 + f["_tow"]
        f["_pickup"] = pu.astype("int64")
        f["_dropoff"] = do.astype("int64")
        return f


class StatisticalEncoder(BaseEstimator, TransformerMixin):
    """빈도 인코딩과 타깃 인코딩을 수행한다.

    타깃 인코딩은 정답(요금)으로 만드는 변수라 그냥 쓰면 정보가 새어나간다.
    두 겹으로 막는다.
      1) train 행에는 K-Fold OOF 값을 넣는다. 자기가 속하지 않은 분할의
         통계만 받으므로 자기 정답이 자기 피처가 되지 않는다.
      2) test 행에는 train 전체 통계를 적용한다.

    인코딩 대상은 요금 자체가 아니라 '마일당 요금'이다. 거리로 정규화하면
    노선·시간대별 정체 수준을 표현하게 된다. 원본 데이터에 소요시간
    컬럼이 없으므로 이 값이 그 대리 변수 역할을 한다.

    다만 RatecodeID 2(JFK 정액)처럼 거리와 무관하게 요금이 고정된 구간에서는
    '단가 x 거리' 가정이 깨진다. 그래서 요금 자체를 인코딩한 변수도 함께 만든다.
    """

    COUNT_SPECS = [("_pickup", "pickup_log_count"),
                   ("_dropoff", "dropoff_log_count"),
                   ("_route", "route_log_count")]

    RATE_SPECS = [("_rc_route", "rc_route_rate"),
                  ("_route", "route_rate"),
                  ("_pickup_tow", "pickup_tow_rate"),
                  ("_rc_tow", "rc_tow_rate")]

    FARE_SPECS = [("_rc_route", "rc_route_fare")]
    MEDIAN_SPECS = [("_rc_route", "rc_route_rate_med")]

    def __init__(self, folds=TE_FOLDS, smoothing=TE_SMOOTHING, seed=SEED):
        """OOF 분할 수, 평활화 강도와 난수 시드를 저장한다."""
        if folds < 2:
            raise ValueError("타깃 인코딩 folds는 2 이상이어야 합니다.")
        if smoothing < 0:
            raise ValueError("타깃 인코딩 smoothing은 0 이상이어야 합니다.")
        self.folds = folds
        self.smoothing = smoothing
        self.seed = seed

    # ── 내부 도우미 ──────────────────────────────────────────────────────
    def _smooth(self, stat: pd.DataFrame, prior: float) -> pd.Series:
        """표본이 적은 그룹을 전체 평균 쪽으로 당긴다.

        노선 조합이 약 19,000개라 몇 건뿐인 노선은 평균이 크게 튄다.
        건수가 적을수록 prior 비중이 커지도록 가중평균한다.
        """
        m = self.smoothing
        return (stat["value"] * stat["count"] + prior * m) / (stat["count"] + m)

    def _group_stat(self, keys, values, use_median=False) -> pd.DataFrame:
        """그룹별 중심값과 관측 수를 하나의 표로 계산한다."""
        grouped = pd.DataFrame({"k": keys, "v": values}).groupby("k")["v"]
        value = grouped.median() if use_median else grouped.mean()
        return pd.DataFrame({"value": value, "count": grouped.size()})

    def _oof(self, keys, values, prior, use_median=False) -> np.ndarray:
        """K-Fold OOF 로 인코딩 값을 채운다."""
        out = np.full(len(keys), np.nan, dtype="float64")
        splitter = KFold(self.folds, shuffle=True, random_state=self.seed)
        for train_idx, valid_idx in splitter.split(out):
            stat = self._group_stat(keys[train_idx], values[train_idx], use_median)
            mapping = self._smooth(stat, prior)
            out[valid_idx] = pd.Series(keys[valid_idx]).map(mapping).to_numpy()
        return np.where(np.isnan(out), prior, out)

    # ── sklearn 인터페이스 ───────────────────────────────────────────────
    def fit(self, X: pd.DataFrame, y=None):
        """train 통계를 학습한다. test 변환에는 이 통계를 그대로 쓴다."""
        target = np.asarray(y, dtype="float64")
        distance = X["trip_distance"].clip(lower=0.1).to_numpy()
        permile = target / distance

        self.count_maps_ = {}
        for key, name in self.COUNT_SPECS:
            self.count_maps_[name] = X[key].value_counts()

        self.rate_prior_ = float(permile.mean())
        self.fare_prior_ = float(target.mean())
        self.median_prior_ = float(np.median(permile))

        self.rate_maps_ = {}
        for key, name in self.RATE_SPECS:
            stat = self._group_stat(X[key].to_numpy(), permile)
            self.rate_maps_[name] = self._smooth(stat, self.rate_prior_)

        self.fare_maps_ = {}
        for key, name in self.FARE_SPECS:
            stat = self._group_stat(X[key].to_numpy(), target)
            self.fare_maps_[name] = self._smooth(stat, self.fare_prior_)

        self.median_maps_ = {}
        for key, name in self.MEDIAN_SPECS:
            stat = self._group_stat(X[key].to_numpy(), permile, use_median=True)
            self.median_maps_[name] = self._smooth(stat, self.median_prior_)

        self.feature_names_ = None          # transform 에서 확정한다
        return self

    def fit_transform(self, X: pd.DataFrame, y=None, **kwargs) -> pd.DataFrame:
        """train 전용 경로. 인코딩 값을 OOF 로 채워 누수를 막는다."""
        self.fit(X, y)
        target = np.asarray(y, dtype="float64")
        distance = X["trip_distance"].clip(lower=0.1).to_numpy()
        permile = target / distance

        out = self._base_frame(X)
        for key, name in self.COUNT_SPECS:
            out[name] = np.log1p(X[key].map(self.count_maps_[name])).astype("float32")

        for key, name in self.RATE_SPECS:
            out[name] = self._oof(X[key].to_numpy(), permile,
                                  self.rate_prior_).astype("float32")
        for key, name in self.FARE_SPECS:
            out[name] = self._oof(X[key].to_numpy(), target,
                                  self.fare_prior_).astype("float32")
        for key, name in self.MEDIAN_SPECS:
            out[name] = self._oof(X[key].to_numpy(), permile, self.median_prior_,
                                  use_median=True).astype("float32")

        return self._finalize(out, X)

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """test 전용 경로. fit 에서 학습한 train 통계를 적용한다."""
        out = self._base_frame(X)
        for key, name in self.COUNT_SPECS:
            mapped = X[key].map(self.count_maps_[name]).fillna(0)
            out[name] = np.log1p(mapped).astype("float32")

        for key, name in self.RATE_SPECS:
            out[name] = X[key].map(self.rate_maps_[name]).fillna(
                self.rate_prior_).astype("float32")
        for key, name in self.FARE_SPECS:
            out[name] = X[key].map(self.fare_maps_[name]).fillna(
                self.fare_prior_).astype("float32")
        for key, name in self.MEDIAN_SPECS:
            out[name] = X[key].map(self.median_maps_[name]).fillna(
                self.median_prior_).astype("float32")

        return self._finalize(out, X)

    @staticmethod
    def _base_frame(X: pd.DataFrame) -> pd.DataFrame:
        """그룹 키(_ 로 시작하는 컬럼)를 뺀 나머지를 그대로 가져온다."""
        keep = [c for c in X.columns if not c.startswith("_")]
        return X[keep].copy()

    @staticmethod
    def _finalize(out: pd.DataFrame, X: pd.DataFrame) -> pd.DataFrame:
        """마일당 단가에 거리를 곱해 '예상 요금' 변수를 만든다.

        원시 단가만으로는 트리가 거의 쓰지 않는다. 거리를 곱해
        실제 금액 단위로 바꿔야 의미 있는 분기 기준이 된다.
        """
        distance = out["trip_distance"].to_numpy()
        out["expected_fare_rc"] = (out["rc_route_rate"] * distance).astype("float32")
        out["expected_fare_route"] = (out["route_rate"] * distance).astype("float32")
        out["expected_fare_tow"] = (out["pickup_tow_rate"] * distance).astype("float32")
        out["expected_fare_med"] = (out["rc_route_rate_med"] * distance).astype("float32")
        return out


def build_model(n_estimators: int, early_stopping: bool):
    """XGBoost 회귀 모델을 만든다.

    objective 는 reg:absoluteerror(L1) 를 쓴다. 평가 지표가 MAE 이므로
    MAE 를 직접 최적화하는 것이 맞다. L2 로 학습하고 MAE 로 채점하면
    다른 것을 최적화해 놓고 다른 것으로 평가받는 셈이 된다.
    """
    return xgb.XGBRegressor(
        objective="reg:absoluteerror",
        eval_metric="mae",
        tree_method="hist",
        n_estimators=n_estimators,
        learning_rate=0.05,
        max_depth=8,
        min_child_weight=20,
        subsample=0.85,
        colsample_bytree=0.9,
        reg_alpha=0.05,
        reg_lambda=2.0,
        max_bin=256,
        early_stopping_rounds=(EARLY_STOPPING_ROUNDS if early_stopping else None),
        random_state=SEED,
        n_jobs=-1,
    )


def evaluate(y_true: np.ndarray, prediction: np.ndarray) -> dict:
    """회귀 평가 지표를 계산한다."""
    error = np.abs(y_true - prediction)
    return {
        "MAE": float(mean_absolute_error(y_true, prediction)),
        "RMSE": float(mean_squared_error(y_true, prediction) ** 0.5),
        "R2": float(r2_score(y_true, prediction)),
        "MAPE_percent": float(np.mean(error / np.maximum(y_true, 1e-6)) * 100),
        "p90_absolute_error": float(np.quantile(error, 0.90)),
        "within_5_dollars_percent": float(np.mean(error <= 5) * 100),
    }


def train_pipeline(train: pd.DataFrame, test: pd.DataFrame) -> tuple:
    """조기 종료로 트리 수를 정한 뒤 전체 train 으로 Pipeline 을 학습한다."""
    if len(train) < max(TE_FOLDS, 10):
        raise ValueError(f"학습 데이터가 너무 적습니다: {len(train)}행")
    if test.empty:
        raise ValueError("평가용 test 데이터가 비어 있습니다.")
    y_train = train[TARGET].astype("float64")
    y_test = test[TARGET].to_numpy()

    # ── 1단계: 앞 85% 로 학습하고 뒤 15% 로 최적 트리 수를 찾는다 ──────────
    # 시간순으로 나눈다. 무작위로 나누면 미래 데이터가 학습에 섞인다.
    split = int(len(train) * (1 - VALIDATION_RATIO))
    log(f"  1단계 조기 종료 (학습 {split:,}행 / 검증 {len(train)-split:,}행)")

    preprocessor = Pipeline([
        ("features", FeatureBuilder()),
        ("encoding", StatisticalEncoder()),
    ])
    # 통계를 앞 85% 에서만 계산해야 검증 구간이 온전한 '미래'가 된다
    tune_X = preprocessor.fit_transform(train.iloc[:split], y_train.iloc[:split])
    valid_X = preprocessor.transform(train.iloc[split:])

    started = time.perf_counter()
    tuner = build_model(MAX_ESTIMATORS, early_stopping=True)
    tuner.fit(tune_X, y_train.iloc[:split],
              eval_set=[(valid_X, y_train.iloc[split:])], verbose=200)
    best_trees = int(tuner.best_iteration) + 1
    log(f"  최적 트리 {best_trees:,}개, 검증 MAE ${tuner.best_score:.4f} "
        f"({time.perf_counter()-started:.1f}초)")
    del tuner, tune_X, valid_X

    # ── 2단계: 트리 수를 고정하고 train 100% 로 다시 학습한다 ──────────────
    # 1단계에서 검증용으로 떼어둔 15% 를 버리지 않기 위함이다.
    log("  2단계 전체 train 재학습")
    started = time.perf_counter()
    pipeline = Pipeline([
        ("features", FeatureBuilder()),
        ("encoding", StatisticalEncoder()),
        ("model", build_model(best_trees, early_stopping=False)),
    ])
    pipeline.fit(train, y_train)
    log(f"  재학습 완료 ({time.perf_counter()-started:.1f}초)")

    prediction = pipeline.predict(test).clip(min=0.75)   # train 최소 요금이 하한
    metrics = evaluate(y_test, prediction)
    return pipeline, prediction, metrics, best_trees


def report_importance(pipeline: Pipeline, sample_X: pd.DataFrame) -> pd.DataFrame:
    """변수 중요도를 gain 기준으로 정리한다.

    gain 은 '그 변수로 분기했을 때 줄어든 손실의 합' 이며, 전체 합이
    100%가 되도록 정규화된 상대 비율이다. 서로 정보가 겹치는 변수가
    있으면 그들 사이에서 임의로 갈리므로, 개별 순위보다 그룹 단위로
    해석하는 편이 안전하다.
    """
    model = pipeline.named_steps["model"]
    features = list(sample_X.columns)

    booster = model.get_booster()
    booster.feature_names = features
    scores = pd.Series(booster.get_score(importance_type="gain"), dtype="float64")
    frame = pd.DataFrame({"gain": scores.reindex(features).fillna(0.0)})
    frame["gain_pct"] = (frame["gain"] / frame["gain"].sum() * 100).round(2)

    encoder = StatisticalEncoder
    rate_names = [n for _, n in encoder.RATE_SPECS]
    fare_names = ([n for _, n in encoder.FARE_SPECS]
                  + [n for _, n in encoder.MEDIAN_SPECS])
    expected = ["expected_fare_rc", "expected_fare_route",
                "expected_fare_tow", "expected_fare_med"]
    count_names = [n for _, n in encoder.COUNT_SPECS]

    def classify(name):
        """개별 피처를 해석 가능한 생성 방식 그룹으로 분류한다."""
        if name in rate_names or name in fare_names or name in expected:
            return "타깃인코딩"
        if name in count_names:
            return "빈도인코딩"
        if name in FeatureBuilder.CYCLIC:
            return "시간(순환)"
        if name in FeatureBuilder.FLAGS:
            return "플래그"
        return "원본"

    frame["group"] = [classify(f) for f in features]
    return frame.sort_values("gain_pct", ascending=False)


def report_error_breakdown(test: pd.DataFrame, prediction: np.ndarray) -> pd.DataFrame:
    """요금제별로 오차가 어디에 몰려 있는지 진단한다."""
    frame = pd.DataFrame({
        "RatecodeID": test["RatecodeID"].to_numpy(),
        "fare": test[TARGET].to_numpy(),
        "abs_err": np.abs(prediction - test[TARGET].to_numpy()),
    })
    diag = frame.groupby("RatecodeID").agg(
        건수=("abs_err", "size"), MAE=("abs_err", "mean"), 평균요금=("fare", "mean"))
    diag["행비중%"] = (diag["건수"] / len(frame) * 100).round(1)
    # 요금 수준이 다른 그룹끼리 비교하려면 절대 오차만으로는 부족하다
    diag["상대오차%"] = (diag["MAE"] / diag["평균요금"] * 100).round(1)
    diag["총오차비중%"] = (frame.groupby("RatecodeID")["abs_err"].sum()
                       / frame["abs_err"].sum() * 100).round(1)
    diag.index = [f"{int(i)}({RATECODE_LABELS.get(int(i), '?')})" for i in diag.index]
    return diag.round(2)


# ══════════════════════════════════════════════════════════════════════════════
# 메인
# ══════════════════════════════════════════════════════════════════════════════
def main() -> None:
    """정제 데이터 로드, 2단계 모델 학습, 평가와 산출물 저장을 실행한다."""
    started = time.perf_counter()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print("NYC Yellow Taxi 요금 예측 - 모델링 파이프라인")
    print("=" * 78)

    log("[1/3] 정제 데이터 로드")
    train = load_data(TRAIN_PATH)
    test = load_data(TEST_PATH)

    if SAMPLE_ROWS > 0:
        train = train.sample(min(SAMPLE_ROWS, len(train)), random_state=SEED)
        train = train.sort_values(TIME_COLUMN).reset_index(drop=True)
        test = test.sample(min(SAMPLE_ROWS // 2, len(test)), random_state=SEED)
        test = test.sort_values(TIME_COLUMN).reset_index(drop=True)
        log(f"  표본 모드: train {len(train):,} / test {len(test):,}")

    log("[2/3] ML Pipeline 학습")
    pipeline, prediction, metrics, best_trees = train_pipeline(train, test)
    y_test = test[TARGET].to_numpy()
    baseline_metrics = evaluate(y_test, np.full_like(y_test, train[TARGET].mean()))

    print("\n" + "=" * 78)
    print("평가 결과")
    print("=" * 78)
    print(f"{'지표':<28}{'베이스라인':>14}{'최종 모델':>14}")
    for key in ["MAE", "RMSE", "R2", "MAPE_percent",
                "p90_absolute_error", "within_5_dollars_percent"]:
        print(f"{key:<28}{baseline_metrics[key]:>14.4f}{metrics[key]:>14.4f}")

    transformed = pipeline.named_steps["encoding"].transform(
        pipeline.named_steps["features"].transform(test.head(100)))
    importance = report_importance(pipeline, transformed)
    error_breakdown = report_error_breakdown(test, prediction)

    log("[3/3] 모델링 산출물 저장")
    model_path = OUTPUT_DIR / "fare_model_pipeline.joblib"
    try:
        joblib.dump(pipeline, model_path)
    except Exception as exc:
        raise RuntimeError(f"학습 모델 저장에 실패했습니다: {model_path}") from exc
    importance.rename_axis("feature").reset_index().to_csv(
        OUTPUT_DIR / "feature_importance.csv", index=False, encoding="utf-8-sig"
    )
    error_breakdown.rename_axis("ratecode").reset_index().to_csv(
        OUTPUT_DIR / "error_by_ratecode.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame({"actual": y_test, "prediction": prediction}).to_csv(
        OUTPUT_DIR / "test_predictions.csv.gz", index=False)

    metrics_payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "elapsed_seconds": time.perf_counter() - started,
        "train_rows": len(train),
        "test_rows": len(test),
        "n_features": transformed.shape[1],
        "best_trees": best_trees,
        "baseline": baseline_metrics,
        "model": metrics,
    }
    (OUTPUT_DIR / "metrics.json").write_text(
        json.dumps(metrics_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    log(f"완료 - 산출물: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
