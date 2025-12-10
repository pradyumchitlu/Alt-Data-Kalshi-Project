"""
Score Kalshi markets with iTunes model + heuristic boosts from Apple/Spotify/YouTube (latest day).
Usage:
  KALSHI_EVENT_TICKER=KXTOPSONG-25DEC20 python3 score_markets.py
"""
from __future__ import annotations

import os
import json
from pathlib import Path

import joblib
import pandas as pd

from kalshi_client import get_event_markets
from train_model import (
    _norm,
    add_itunes_features,
    load_itunes,
    load_spotify,
    load_apple,
    load_youtube,
)

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "billboard_rf.pkl"
FEAT_PATH = MODELS_DIR / "feature_columns.json"


def latest_by_key(df: pd.DataFrame, value_cols):
    if df.empty:
        return pd.DataFrame(columns=["key"] + value_cols)
    latest_date = df["collection_date"].max()
    sub = df[df["collection_date"] == latest_date].copy()
    return sub[["key"] + value_cols]


def load_model():
    if not MODEL_PATH.exists() or not FEAT_PATH.exists():
        raise SystemExit("Model artifacts missing; run train_model.py first.")
    model = joblib.load(MODEL_PATH)
    feature_cols = json.load(open(FEAT_PATH))
    return model, feature_cols


def heuristic_boost(row, apple, spotify, youtube):
    boost = 0.0
    key = row["key"]

    # Apple rank / streams
    if key in apple.index:
        streams = apple.loc[key, "am_streams"]
        pos = apple.loc[key, "am_chart_position"]
        if pd.notna(pos) and pos > 0:
            if pos <= 5:
                boost += 0.08
            elif pos <= 10:
                boost += 0.05
            elif pos <= 20:
                boost += 0.02
        if pd.notna(streams) and streams > 0:
            boost += min(0.05, streams / (apple["am_streams"].max() + 1e-9) * 0.05)

    # Spotify streams
    if key in spotify.index:
        streams = spotify.loc[key, "sp_streams"]
        if pd.notna(streams) and streams > 0:
            boost += min(0.05, streams / (spotify["sp_streams"].max() + 1e-9) * 0.05)

    # YouTube views
    if key in youtube.index:
        views = youtube.loc[key, "views"]
        if pd.notna(views) and views > 0:
            boost += min(0.03, views / (youtube["views"].max() + 1e-9) * 0.03)

    return boost


def main():
    event = os.getenv("KALSHI_EVENT_TICKER", "KXTOPSONG-25DEC20")
    markets = get_event_markets(event)
    print(f"Markets found for {event}: {len(markets)}")

    # Load model
    model, feature_cols = load_model()

    # Load latest features
    itunes = add_itunes_features(load_itunes())
    latest_date = itunes["collection_date"].max()
    latest_itunes = itunes[itunes["collection_date"] == latest_date].copy()
    latest_itunes["key"] = latest_itunes["key"]
    itunes_idx = latest_itunes.set_index("key")

    # Latest Apple/Spotify/YouTube
    apple = latest_by_key(load_apple(), ["am_streams", "am_chart_position"]).set_index("key")
    spotify = latest_by_key(load_spotify(), ["sp_streams", "sp_chart_position"]).set_index("key")
    youtube = latest_by_key(load_youtube(), ["views"]).set_index("key")

    rows = []
    for m in markets:
        subtitle = m.get("subtitle", "")
        ticker = m.get("ticker")
        if "::" in subtitle:
            song, artist = subtitle.split("::", 1)
        else:
            song = subtitle
            artist = ""
        key = _norm(song) + "||" + _norm(artist)

        base_prob = None
        ds = None
        if key in itunes_idx.index:
            try:
                base_prob = model.predict_proba(itunes_idx.loc[[key], feature_cols])[:, 1].max()
            except KeyError:
                # If some optional columns missing, fill them on the fly
                row = itunes_idx.loc[[key]].copy()
                for col in feature_cols:
                    if col not in row.columns:
                        row[col] = 0
                base_prob = model.predict_proba(row[feature_cols])[:, 1].max()
            ds = itunes_idx.loc[key, "digital_sales"] if "digital_sales" in itunes_idx else None

        boost = heuristic_boost({"key": key}, apple, spotify, youtube)
        final_prob = None if base_prob is None else min(1.0, base_prob + boost)

        rows.append(
            {
                "ticker": ticker,
                "song": song.strip(),
                "artist": artist.strip(),
                "base_prob": base_prob,
                "boost": boost,
                "final_prob": final_prob,
                "digital_sales": ds,
            }
        )

    print(f"Latest iTunes date: {latest_date.date()}")
    print("Ticker | Base_P | Boost | Final_P | DigitalSales | Song — Artist")
    for r in rows:
        print(
            f"{r['ticker']:>22} | "
            f"{r['base_prob'] if r['base_prob'] is not None else 'NA':>6} | "
            f"{r['boost']:.3f} | "
            f"{r['final_prob'] if r['final_prob'] is not None else 'NA':>6} | "
            f"{r['digital_sales'] if r['digital_sales'] is not None else 'NA':>12} | "
            f"{r['song']} — {r['artist']}"
        )


if __name__ == "__main__":
    main()

