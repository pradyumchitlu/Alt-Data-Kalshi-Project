from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


# ------------- PATHS -------------

# baseline_climatology_model.py -> models -> src -> project root
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_PROCESSED_DIR = ROOT_DIR / "data_processed"


def load_climatology_features() -> pd.DataFrame:
    path = DATA_PROCESSED_DIR / "climatology_features.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run build_climatology_features first."
        )
    df = pd.read_parquet(path)
    df["target_date"] = pd.to_datetime(df["target_date"]).dt.normalize()
    df = df.sort_values("target_date").reset_index(drop=True)
    return df


def train_test_split_time(df: pd.DataFrame, test_frac: float = 0.2):
    """Time-aware split: first (1 - test_frac) for train, last test_frac for test."""
    n = len(df)
    n_test = int(n * test_frac)
    n_train = n - n_test
    df_train = df.iloc[:n_train].copy()
    df_test = df.iloc[n_train:].copy()
    return df_train, df_test


def build_feature_matrices(df: pd.DataFrame):
    """Build X, y arrays from feature table."""

    feature_cols = [
        c for c in df.columns if c not in ["target_date", "tmax_F"]
    ]

    X = df[feature_cols].astype(float).copy()
    y = df["tmax_F"].astype(float).values

    # Fill NaNs if any appear
    X = X.fillna(X.mean())

    return X, y, feature_cols


def rmse(y_true, y_pred):
    """Manual RMSE for compatibility with older sklearn."""
    return np.sqrt(mean_squared_error(y_true, y_pred))


def evaluate_baseline_and_model():
    df = load_climatology_features()
    df_train, df_test = train_test_split_time(df, test_frac=0.2)

    print(f"Total rows: {len(df)}")
    print(f"Train rows: {len(df_train)}  (up to {df_train['target_date'].iloc[-1].date()})")
    print(f"Test rows : {len(df_test)}  (from {df_test['target_date'].iloc[0].date()} onward)\n")

    # ----------------- BASELINE (tmax_F_lag_1) -----------------
    y_train_true = df_train["tmax_F"].values
    y_test_true = df_test["tmax_F"].values

    y_train_naive = df_train["tmax_F_lag_1"].values
    y_test_naive = df_test["tmax_F_lag_1"].values

    mae_train_naive = mean_absolute_error(y_train_true, y_train_naive)
    mae_test_naive = mean_absolute_error(y_test_true, y_test_naive)

    rmse_train_naive = rmse(y_train_true, y_train_naive)
    rmse_test_naive = rmse(y_test_true, y_test_naive)

    print("=== Naive baseline (predict yesterday’s high) ===")
    print(f"Train MAE : {mae_train_naive:6.3f}")
    print(f"Test  MAE : {mae_test_naive:6.3f}")
    print(f"Train RMSE: {rmse_train_naive:6.3f}")
    print(f"Test  RMSE: {rmse_test_naive:6.3f}\n")

    # ----------------- RandomForest MODEL -----------------
    X_train, y_train, feature_cols = build_feature_matrices(df_train)
    X_test, y_test, _ = build_feature_matrices(df_test)

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)

    mae_train = mean_absolute_error(y_train, y_train_pred)
    mae_test = mean_absolute_error(y_test, y_test_pred)

    rmse_train = rmse(y_train, y_train_pred)
    rmse_test = rmse(y_test, y_test_pred)

    print("=== RandomForest Model (climatology features) ===")
    print(f"Train MAE : {mae_train:6.3f}")
    print(f"Test  MAE : {mae_test:6.3f}")
    print(f"Train RMSE: {rmse_train:6.3f}")
    print(f"Test  RMSE: {rmse_test:6.3f}\n")

    # ----------------- Show sample predictions -----------------
    df_out = df_test[["target_date", "tmax_F"]].copy()
    df_out["pred_naive"] = y_test_naive
    df_out["pred_model"] = y_test_pred
    df_out["err_naive"] = df_out["pred_naive"] - df_out["tmax_F"]
    df_out["err_model"] = df_out["pred_model"] - df_out["tmax_F"]

    print("Sample test predictions (last 10 days):")
    print(
        df_out.tail(10)
        .round({"tmax_F": 1, "pred_naive": 1, "pred_model": 1, "err_naive": 1, "err_model": 1})
    )

    return df_out


def main():
    evaluate_baseline_and_model()


if __name__ == "__main__":
    main()
