from __future__ import annotations

from pathlib import Path
import math

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


# ---------- PATHS ----------

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
    n = len(df)
    n_test = int(n * test_frac)
    n_train = n - n_test
    df_train = df.iloc[:n_train].copy()
    df_test = df.iloc[n_train:].copy()
    return df_train, df_test


def build_feature_matrices(df: pd.DataFrame):
    feature_cols = [c for c in df.columns if c not in ["target_date", "tmax_F"]]
    X = df[feature_cols].astype(float).copy()
    y = df["tmax_F"].astype(float).values
    X = X.fillna(X.mean())
    return X, y, feature_cols


def rmse(y_true, y_pred):
    return math.sqrt(mean_squared_error(y_true, y_pred))


def estimate_error_distribution():
    """
    Train the climatology RF model (like before), estimate error distribution
    on the held-out test set, and return sigma (std of residuals).
    """
    df = load_climatology_features()
    df_train, df_test = train_test_split_time(df, test_frac=0.2)

    X_train, y_train, feat_cols = build_feature_matrices(df_train)
    X_test, y_test, _ = build_feature_matrices(df_test)

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_test_pred = model.predict(X_test)
    residuals = y_test_pred - y_test

    mae = mean_absolute_error(y_test, y_test_pred)
    sigma = float(np.std(residuals, ddof=1))  # sample std

    print(f"Test MAE (RF climatology): {mae:6.3f} °F")
    print(f"Estimated sigma (std of residuals): {sigma:6.3f} °F")

    return model, sigma, df_test, y_test, y_test_pred


# ---------- Normal CDF / bracket probs ----------

def normal_cdf(x: float, mean: float = 0.0, std: float = 1.0) -> float:
    """
    Standard normal CDF using error function.
    """
    z = (x - mean) / (std * math.sqrt(2.0))
    return 0.5 * (1.0 + math.erf(z))


def bracket_probs(
    mean: float,
    sigma: float,
    brackets: list[tuple[float | None, float | None]],
) -> list[float]:
    """
    Given a Normal(mu=mean, sigma), compute probability mass in each bracket.

    Each bracket is (low, high) where low or high can be None for -inf/+inf.
    """
    probs: list[float] = []
    for low, high in brackets:
        if low is None:
            cdf_low = 0.0
        else:
            cdf_low = normal_cdf(low, mean=mean, std=sigma)

        if high is None:
            cdf_high = 1.0
        else:
            cdf_high = normal_cdf(high, mean=mean, std=sigma)

        probs.append(max(0.0, min(1.0, cdf_high - cdf_low)))
    # Normalize just in case of numeric drift
    total = sum(probs)
    if total > 0:
        probs = [p / total for p in probs]
    return probs


def example_for_today(model, sigma: float):
    """
    Construct features for the most recent day in the climatology table,
    get the model's prediction for 'tomorrow', and compute bracket probabilities
    for some example Kalshi-style brackets.

    NOTE: This is just a demo using the last row in the dataset
          as if we were forecasting the next day.
    """
    path = DATA_PROCESSED_DIR / "climatology_features.parquet"
    df = pd.read_parquet(path).sort_values("target_date").reset_index(drop=True)

    # Use the last row as "today" features
    row = df.iloc[-1].copy()
    today = row["target_date"]
    true_today = row["tmax_F"]

    # Build X for just this row
    feature_cols = [c for c in df.columns if c not in ["target_date", "tmax_F"]]
    x_today = row[feature_cols].astype(float).values.reshape(1, -1)
    pred_today = float(model.predict(x_today)[0])

    print("\n--- Example: using last available day as 'today' ---")
    print(f"Date: {today.date()}, true high: {true_today:.1f} °F")
    print(f"Model point forecast (from climatology): {pred_today:.1f} °F")

    # Example bracket design:
    # Let's say Kalshi-like brackets around the model mean, width 2°F:
    # (..., <= μ-4), (μ-4, μ-2], (μ-2, μ], (μ, μ+2], (μ+2, μ+4], (> μ+4, ...)
    mu = pred_today
    brackets = [
        (None, mu - 4),      # very cool
        (mu - 4, mu - 2),    # cool
        (mu - 2, mu),        # slightly cool
        (mu, mu + 2),        # slightly warm
        (mu + 2, mu + 4),    # warm
        (mu + 4, None),      # very warm
    ]

    probs = bracket_probs(mu, sigma, brackets)

    print("\nBracket probabilities (example, purely from climatology RF):")
    for (low, high), p in zip(brackets, probs):
        if low is None:
            label = f"(-inf, {high:.1f}]"
        elif high is None:
            label = f"({low:.1f}, +inf)"
        else:
            label = f"({low:.1f}, {high:.1f}]"
        print(f"{label:>18}: {p*100:5.1f} %")

    return {
        "today": today,
        "true_today": true_today,
        "pred_today": pred_today,
        "sigma": sigma,
        "brackets": brackets,
        "probs": probs,
    }


def main():
    model, sigma, df_test, y_test, y_test_pred = estimate_error_distribution()
    _ = example_for_today(model, sigma)


if __name__ == "__main__":
    main()
