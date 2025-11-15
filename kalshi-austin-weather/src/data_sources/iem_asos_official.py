from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from .nws_official import ROOT_DIR  # reuse ROOT_DIR from before

DATA_PROCESSED_DIR = ROOT_DIR / "data_processed"
DATA_PROCESSED_DIR.mkdir(exist_ok=True)

IEM_ASOS_URL = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"


def fetch_iem_asos_kaus_daily_max(
    start_date: dt.date,
    end_date: dt.date,
    tz: str = "Etc/UTC",
) -> pd.DataFrame:
    """
    Fetch multi-year ASOS observations for KAUS from the IEM archive and
    compute daily max temperature (F).

    Uses the Iowa Environmental Mesonet ASOS request interface.
    """
    params = {
        "station": "KAUS",
        "data": "tmpf",          # temperature in Fahrenheit
        "year1": start_date.year,
        "month1": start_date.month,
        "day1": start_date.day,
        "year2": end_date.year,
        "month2": end_date.month,
        "day2": end_date.day,
        "tz": tz,
        "format": "onlycsv",
        "latlon": "no",
        "direct": "no",
    }

    print(f"Requesting IEM ASOS data for KAUS from {start_date} to {end_date}...")
    resp = requests.get(IEM_ASOS_URL, params=params, timeout=60)
    resp.raise_for_status()

    from io import StringIO
    csv_text = resp.text

    # Some responses include comment lines starting with '#'
    df_raw = pd.read_csv(
        StringIO(csv_text),
        comment="#",
    )

    if df_raw.empty:
        raise RuntimeError("No rows returned from IEM ASOS for the given range.")

    if "valid" not in df_raw.columns or "tmpf" not in df_raw.columns:
        raise RuntimeError(
            f"Unexpected columns in IEM response; got: {df_raw.columns.tolist()}"
        )

    # Parse datetime and date
    df_raw["valid"] = pd.to_datetime(df_raw["valid"])
    df_raw["date"] = df_raw["valid"].dt.date

    # Force temperature to numeric; coerce invalid entries to NaN
    df_raw["tmpf"] = pd.to_numeric(df_raw["tmpf"], errors="coerce")

    # Drop rows with missing temps
    df_raw = df_raw.dropna(subset=["tmpf"])

    # Compute daily max
    df_daily = (
        df_raw.groupby("date", as_index=False)["tmpf"]
        .max()
        .rename(columns={"tmpf": "tmax_F"})
    )

    # Ensure clean types
    df_daily["tmax_F"] = df_daily["tmax_F"].astype(float)
    df_daily["date"] = pd.to_datetime(df_daily["date"]).dt.date

    df_daily["station_id"] = "KAUS"
    df_daily["source"] = "IEM_ASOS_MAX"

    # Reorder columns
    df_daily = df_daily[["date", "station_id", "tmax_F", "source"]]

    return df_daily


def save_iem_as_official_parquet(
    start_date: dt.date,
    end_date: dt.date,
    merge_with_existing: bool = True,
) -> pd.DataFrame:
    """
    Fetch KAUS daily max temps from IEM and write to
    data_processed/official_highs_kaus.parquet

    If merge_with_existing=True and the file already exists, merges and
    deduplicates by date.
    """
    df_new = fetch_iem_asos_kaus_daily_max(start_date, end_date)

    out_path = DATA_PROCESSED_DIR / "official_highs_kaus.parquet"

    if merge_with_existing and out_path.exists():
        df_existing = pd.read_parquet(out_path)

        # Normalize tmax_F to float in existing file too
        if "tmax_F" in df_existing.columns:
            df_existing["tmax_F"] = pd.to_numeric(
                df_existing["tmax_F"], errors="coerce"
            ).astype(float)

        df_all = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_all = df_new.copy()

    # Final cleanup: enforce types & drop bad rows
    df_all["tmax_F"] = pd.to_numeric(df_all["tmax_F"], errors="coerce")
    df_all = df_all.dropna(subset=["tmax_F"])
    df_all["tmax_F"] = df_all["tmax_F"].astype(float)

    df_all["date"] = pd.to_datetime(df_all["date"]).dt.date
    df_all["station_id"] = df_all["station_id"].astype(str)
    df_all["source"] = df_all["source"].astype(str)

    # Drop duplicate dates, keep last (IEM should dominate)
    df_all = (
        df_all.drop_duplicates(subset=["date"], keep="last")
        .sort_values("date")
        .reset_index(drop=True)
    )

    out_path.parent.mkdir(exist_ok=True)
    df_all.to_parquet(out_path, index=False)
    print(f"Saved {len(df_all)} days of highs to {out_path}")

    return df_all


def main():
    # Backfill from 2020-01-01 to today
    end = dt.date.today()
    start = dt.date(2020, 1, 1)
    print(f"Backfilling KAUS daily highs via IEM from {start} to {end}")
    save_iem_as_official_parquet(start, end, merge_with_existing=True)


if __name__ == "__main__":
    main()
