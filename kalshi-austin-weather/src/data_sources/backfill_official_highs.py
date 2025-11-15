from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import requests
from requests import exceptions as req_exc

from .nws_official import fetch_official_highs_kaus, ROOT_DIR


DATA_PROCESSED_DIR = ROOT_DIR / "data_processed"
DATA_PROCESSED_DIR.mkdir(exist_ok=True)


def backfill_official_highs(
    start_date: dt.date,
    end_date: dt.date,
    chunk_days: int = 5,
) -> pd.DataFrame:
    """
    Backfill daily max temps for KAUS between start_date and end_date,
    fetching in small chunks to be nice to the NWS API.

    Returns a DataFrame and writes it to:
        data_processed/official_highs_kaus.parquet
    """
    all_chunks: list[pd.DataFrame] = []

    cur = start_date
    while cur <= end_date:
        chunk_end = min(cur + dt.timedelta(days=chunk_days - 1), end_date)
        print(f"Fetching {cur} → {chunk_end}...")

        try:
            df_chunk = fetch_official_highs_kaus(cur, chunk_end)
        except (req_exc.RequestException, RuntimeError) as e:
            print(f"!! Failed chunk {cur} → {chunk_end}: {e}")
            cur = chunk_end + dt.timedelta(days=1)
            continue

        if df_chunk.empty:
            print(f"   (no observations returned for this range)")
        else:
            print(f"   (got {len(df_chunk)} days)")
            all_chunks.append(df_chunk)

        cur = chunk_end + dt.timedelta(days=1)

    if not all_chunks:
        raise RuntimeError("No data returned from NWS for the given range.")

    df = pd.concat(all_chunks, ignore_index=True)

    # Drop duplicate dates just in case and sort
    df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)

    out_path = DATA_PROCESSED_DIR / "official_highs_kaus.parquet"
    df.to_parquet(out_path, index=False)
    print(f"\nSaved {len(df)} days of highs to {out_path}")

    return df


def main():
    # For now, only grab the last 30 days (NWS obs endpoint doesn't expose long history)
    end = dt.date.today()
    start = end - dt.timedelta(days=30)

    print(f"Backfilling KAUS official highs from {start} to {end}")
    backfill_official_highs(start, end)


if __name__ == "__main__":
    main()
