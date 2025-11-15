from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd


# ---------------- PATHS ----------------

# project root: build_climatology_features.py -> features -> src -> project root
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_PROCESSED_DIR = ROOT_DIR / "data_processed"


def build_climatology_features(
    min_history_days: int = 7,
) -> pd.DataFrame:
    """
    Build a purely historical/climatology-based feature table from
    official_highs_kaus.parquet.

    For each target_date, features are computed using ONLY PAST DAYS:
      - tmax_F           : actual max temp (label)
      - tmax_F_lag_1     : previous day's max temp
      - tmax_F_rm3       : rolling mean of last 3 days (excluding today)
      - tmax_F_rm7       : rolling mean of last 7 days (excluding today)
      - month, dayofyear, dow
      - sin_doy, cos_doy : cyclic seasonal features
    """
    highs_path = DATA_PROCESSED_DIR / "official_highs_kaus.parquet"
    if not highs_path.exists():
        raise FileNotFoundError(
            f"Could not find {highs_path}. "
            "Make sure you ran iem_asos_official first."
        )

    df = pd.read_parquet(highs_path)

    # Ensure expected columns
    if "date" not in df.columns or "tmax_F" not in df.columns:
        raise RuntimeError(
            f"official_highs_kaus.parquet missing required columns. "
            f"Found: {df.columns.tolist()}"
        )

    # Clean types
    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    df["tmax_F"] = pd.to_numeric(df["tmax_F"], errors="coerce")
    df = df.dropna(subset=["tmax_F"])

    # Sort by date
    df = df.sort_values("date").reset_index(drop=True)

    # Set index for convenience
    df = df.set_index("date")

    # ---- Lag and rolling features (using only past data) ----
    # For forecasting day D, we want:
    #   lag_1 = tmax on D-1
    #   rm3   = mean(tmax on D-1, D-2, D-3)
    #   rm7   = mean(tmax on D-1..D-7)
    tmax = df["tmax_F"]

    df["tmax_F_lag_1"] = tmax.shift(1)
    df["tmax_F_rm3"] = tmax.rolling(window=3).mean().shift(1)
    df["tmax_F_rm7"] = tmax.rolling(window=7).mean().shift(1)

    # ---- Calendar features ----
    idx = df.index
    df["month"] = idx.month
    df["dayofyear"] = idx.dayofyear
    df["dow"] = idx.weekday  # 0=Mon, 6=Sun

    # Cyclic encoding of day-of-year
    # 2π * (dayofyear / 366) to roughly handle leap years
    angle = 2 * np.pi * (df["dayofyear"] / 366.0)
    df["sin_doy"] = np.sin(angle)
    df["cos_doy"] = np.cos(angle)

    # ---- Final cleanup ----
    # Drop rows that don't have enough history (NaNs from lags/rolls)
    df = df.dropna(
        subset=["tmax_F_lag_1", "tmax_F_rm3", "tmax_F_rm7"]
    ).copy()

    # Optionally ensure we have at least `min_history_days` total rows
    if len(df) < min_history_days:
        raise RuntimeError(
            f"Not enough history to build features "
            f"(only {len(df)} usable days after lag/rolling)."
        )

    # Reset index and rename for consistency with other tables
    df = df.reset_index().rename(columns={"date": "target_date"})

    # Reorder columns for readability
    cols = [
        "target_date",
        "tmax_F",          # label
        "tmax_F_lag_1",
        "tmax_F_rm3",
        "tmax_F_rm7",
        "month",
        "dayofyear",
        "dow",
        "sin_doy",
        "cos_doy",
    ]
    df = df[cols]

    out_path = DATA_PROCESSED_DIR / "climatology_features.parquet"
    df.to_parquet(out_path, index=False)

    print(f"Built climatology feature table with {len(df)} rows.")
    print(f"Saved to: {out_path}")
    print(df.tail())

    return df


def main():
    build_climatology_features()


if __name__ == "__main__":
    main()
