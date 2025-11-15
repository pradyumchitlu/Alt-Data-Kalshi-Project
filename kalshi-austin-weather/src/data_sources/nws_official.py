from __future__ import annotations

import datetime as dt
from typing import Iterable
import time
from pathlib import Path

import pandas as pd
import requests
from requests import exceptions as req_exc

# ----------------- PATHS / CONFIG -----------------

# project root: nws_official.py -> data_sources -> src -> project root
ROOT_DIR = Path(__file__).resolve().parents[2]

DATA_PROCESSED_DIR = ROOT_DIR / "data_processed"
DATA_PROCESSED_DIR.mkdir(exist_ok=True)

STATION_ID = "KAUS"
LAT = 30.1944
LON = -97.67

NWS_BASE = "https://api.weather.gov"


# ----------------- UTILITIES -----------------

def daterange(start: dt.date, end: dt.date) -> Iterable[dt.date]:
    """Inclusive date range generator."""
    cur = start
    while cur <= end:
        yield cur
        cur += dt.timedelta(days=1)


def _get_json_with_retries(
    url: str,
    headers: dict,
    timeout: int = 25,
    max_retries: int = 3,
    pause: int = 2,
):
    """
    GET a URL and return JSON with simple retry & backoff.
    Raises the last exception if all retries fail.
    """
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except req_exc.RequestException as e:
            if attempt == max_retries:
                print(f"ERROR: {url} failed after {max_retries} attempts")
                raise
            sleep_sec = pause * attempt
            print(
                f"Request failed (attempt {attempt}/{max_retries}): {e}. "
                f"Retrying in {sleep_sec}s..."
            )
            time.sleep(sleep_sec)


# ----------------- OFFICIAL DAILY HIGH -----------------

def fetch_official_highs_kaus(
    start_date: dt.date,
    end_date: dt.date,
) -> pd.DataFrame:
    """
    Fetch daily max temperatures for KAUS between start_date and end_date.
    Uses the NWS observations endpoint as a proxy for the official high
    (max of all temperature observations for that day).
    """
    records = []

    headers = {
        "User-Agent": "austin-temp-research (aarav.mohanty23@gmail.com)"
    }

    for day in daterange(start_date, end_date):
        start_iso = dt.datetime.combine(day, dt.time.min).isoformat() + "Z"
        end_iso = dt.datetime.combine(day, dt.time.max).isoformat() + "Z"

        url = (
            f"{NWS_BASE}/stations/{STATION_ID}/observations"
            f"?start={start_iso}&end={end_iso}"
        )

        data = _get_json_with_retries(
            url, headers=headers, timeout=25, max_retries=3
        )

        temps_F = []
        for feat in data.get("features", []):
            props = feat.get("properties", {})
            temp_c = props.get("temperature", {}).get("value")
            if temp_c is None:
                continue
            temps_F.append(temp_c * 9 / 5 + 32)

        if temps_F:
            tmax_F = max(temps_F)
            records.append(
                {
                    "date": day,
                    "station_id": STATION_ID,
                    "tmax_F": tmax_F,
                    "source": "NWS_OBS_MAX",  # later you can swap to true CLI
                }
            )

    df = pd.DataFrame.from_records(records)
    return df


# ----------------- POINT FORECAST (baseline) -----------------

def fetch_point_forecasts_kaus() -> pd.DataFrame:
    """
    Fetch current NWS point forecast for the KAUS location and turn it into
    a table of (issue_time, target_date, forecast_high_F).
    """
    headers = {
        "User-Agent": "austin-temp-research (aarav.mohanty23@gmail.com)"
    }

    # 1) Get the gridpoint for this lat/lon
    points_url = f"{NWS_BASE}/points/{LAT},{LON}"
    points = _get_json_with_retries(points_url, headers=headers)

    forecast_url = points["properties"]["forecast"]  # daily periods
    forecast = _get_json_with_retries(forecast_url, headers=headers)

    props = forecast.get("properties", {})

    # Try several possible keys; fall back to "now" if none exist
    issue_raw = (
        props.get("updated")
        or props.get("generatedAt")
        or props.get("updateTime")
    )

    if issue_raw is not None:
        issue_time = pd.to_datetime(issue_raw)
    else:
        issue_time = pd.Timestamp.utcnow()

    rows = []
    periods = props.get("periods", [])

    for period in periods:
        start_time = pd.to_datetime(period["startTime"])
        target_date = start_time.date()
        temp_F = period["temperature"]
        is_daytime = period["isDaytime"]

        # Use only the daytime periods as the forecast high
        if not is_daytime:
            continue

        rows.append(
            {
                "issue_time_utc": issue_time,
                "target_date": target_date,
                "forecast_high_F": float(temp_F),
                "source": "NWS_POINT_FORECAST",
            }
        )

    return pd.DataFrame(rows)


# ----------------- MAIN (manual test) -----------------

def main():
    # Example: last 7 days of highs
    today = dt.date.today()
    start = today - dt.timedelta(days=7)
    highs = fetch_official_highs_kaus(start, today)
    print("Official highs:")
    print(highs.tail())

    forecasts = fetch_point_forecasts_kaus()
    print("\nCurrent point-forecast highs:")
    print(forecasts.head())

    # Save to disk at project root /data_processed
    highs.to_parquet(
        DATA_PROCESSED_DIR / "official_highs_kaus.parquet",
        index=False,
    )
    forecasts.to_parquet(
        DATA_PROCESSED_DIR / "nws_point_forecast_kaus.parquet",
        index=False,
    )

    print("\nSaved parquet files to data_processed/.")


if __name__ == "__main__":
    main()
