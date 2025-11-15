from __future__ import annotations

from pathlib import Path

import pandas as pd


# ------------- PATHS -----------------

# project root: build_daily_features.py -> features -> src -> project root
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_PROCESSED_DIR = ROOT_DIR / "data_processed"


def build_daily_features() -> pd.DataFrame:
    """
    Join official highs + NWS point forecasts into a single daily feature table.

    Output columns (for now):
        target_date          - the day we're predicting
        tmax_F               - observed max temp (label)
        forecast_high_F      - NWS point forecast high
        issue_time_utc       - when the forecast was issued
        month, dayofyear, dow - simple calendar features
    """
    highs_path = DATA_PROCESSED_DIR / "official_highs_kaus.parquet"
    fcst_path = DATA_PROCESSED_DIR / "nws_point_forecast_kaus.parquet"

    df_highs = pd.read_parquet(highs_path)
    df_fcst = pd.read_parquet(fcst_path)

    # Normalize column names / types
    # df_highs has: date, station_id, tmax_F, source
    df_highs = df_highs.rename(columns={"date": "target_date"})
    df_highs["target_date"] = pd.to_datetime(df_highs["target_date"]).dt.normalize()

    # df_fcst has: issue_time_utc, target_date, forecast_high_F, source
    df_fcst["target_date"] = pd.to_datetime(df_fcst["target_date"]).dt.normalize()
    df_fcst["issue_time_utc"] = pd.to_datetime(df_fcst["issue_time_utc"])

    # For now, just use the latest forecast per target_date (max issue_time_utc)
    df_fcst_sorted = df_fcst.sort_values(["target_date", "issue_time_utc"])
    df_fcst_latest = (
        df_fcst_sorted.groupby("target_date").tail(1).reset_index(drop=True)
    )

    # Inner join: only days where we have both obs + forecast
    df = pd.merge(
        df_highs,
        df_fcst_latest,
        on="target_date",
        how="inner",
        suffixes=("_obs", "_fcst"),
    )

    # Drop some metadata columns we don't need right now
    df = df.drop(columns=["station_id", "source_obs", "source_fcst"], errors="ignore")

    # Calendar features
    df["month"] = df["target_date"].dt.month
    df["dayofyear"] = df["target_date"].dt.dayofyear
    df["dow"] = df["target_date"].dt.weekday  # 0=Monday

    # Reorder columns for readability
    cols = [
        "target_date",
        "tmax_F",           # label
        "forecast_high_F",  # baseline feature
        "issue_time_utc",
        "month",
        "dayofyear",
        "dow",
    ]
    df = df[cols]

    out_path = DATA_PROCESSED_DIR / "daily_features.parquet"
    df.to_parquet(out_path, index=False)

    print(f"Built daily feature table with {len(df)} rows.")
    print(f"Saved to: {out_path}")
    print(df.tail())

    return df


def main():
    build_daily_features()


if __name__ == "__main__":
    main()
