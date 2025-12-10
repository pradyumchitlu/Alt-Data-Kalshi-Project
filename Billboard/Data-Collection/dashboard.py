"""
Streamlit dashboard:
- Shows top predicted #1 candidates from latest iTunes features
- Compares model probabilities to Kalshi prices, highlights +EV
- Run: streamlit run dashboard.py
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import altair as alt
import joblib
import pandas as pd
import streamlit as st

from kalshi_client import get_event_markets, get_market_orderbook
from train_model import (
    _norm,
    add_itunes_features,
    load_itunes,
    load_apple,
    load_spotify,
    load_youtube,
)

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
MODEL_PATH = MODELS_DIR / "billboard_rf.pkl"
FEATURE_FILE = MODELS_DIR / "feature_columns.json"
METRICS_PATH = MODELS_DIR / "training_metrics.json"


def load_model():
    if not MODEL_PATH.exists() or not FEATURE_FILE.exists():
        st.error("Model not found. Run `python3 train_model.py` first.")
        return None, None
    model = joblib.load(MODEL_PATH)
    with open(FEATURE_FILE) as f:
        feature_cols = json.load(f)
    return model, feature_cols


def load_metrics():
    if not METRICS_PATH.exists():
        return None
    try:
        with open(METRICS_PATH) as f:
            return json.load(f)
    except Exception:
        return None


def build_latest_feature_frame():
    itunes = add_itunes_features(load_itunes())
    latest_date = itunes["collection_date"].max()
    latest = itunes[itunes["collection_date"] == latest_date].copy()
    latest["key"] = latest["key"]
    return latest, latest_date


def latest_by_key(df: pd.DataFrame, value_cols):
    if df.empty:
        return pd.DataFrame(columns=["key"] + value_cols)
    latest_date = df["collection_date"].max()
    sub = df[df["collection_date"] == latest_date].copy()
    return sub[["key"] + value_cols]


def predict_latest(model, feature_cols):
    latest, latest_date = build_latest_feature_frame()
    latest["prob_yes1"] = model.predict_proba(latest[feature_cols])[:, 1]
    latest = latest.sort_values("prob_yes1", ascending=False)
    return latest, latest_date


def heuristic_boost(key, apple, spotify, youtube):
    boost = 0.0
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
    if key in spotify.index:
        streams = spotify.loc[key, "sp_streams"]
        if pd.notna(streams) and streams > 0:
            boost += min(0.05, streams / (spotify["sp_streams"].max() + 1e-9) * 0.05)
    if key in youtube.index:
        views = youtube.loc[key, "views"]
        if pd.notna(views) and views > 0:
            boost += min(0.03, views / (youtube["views"].max() + 1e-9) * 0.03)
    return boost


def _fmt_pct(x):
    return f"{x:.1%}" if pd.notna(x) else "—"


def render_kalshi(event_ticker: str):
    st.subheader("Kalshi Markets")
    try:
        markets = get_event_markets(event_ticker)
        st.caption(f"Retrieved {len(markets)} markets for event {event_ticker}")
        return markets
    except Exception as e:
        st.error(f"Kalshi API error: {e}")
        return []


def render_orderbook(ticker: str):
    # Orderbook display removed per request
    return


def _inject_css():
    st.markdown(
        """
        <style>
        :root {
            --bg: #07090f;
            --card: #0f1320;
            --accent: #7c5dff;
            --accent2: #12c2e9;
            --text: #e9ecf5;
            --muted: #9aa2b5;
        }
        .stApp {
            background: radial-gradient(circle at 20% 20%, rgba(124,93,255,0.25), transparent 30%),
                        radial-gradient(circle at 80% 10%, rgba(18,194,233,0.25), transparent 30%),
                        radial-gradient(circle at 30% 80%, rgba(124,93,255,0.15), transparent 35%),
                        #07090f;
            color: var(--text);
        }
        .block-container { padding-top: 2rem; }
        .glass {
            background: rgba(15,19,32,0.8);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 16px;
            padding: 1rem 1.2rem;
            box-shadow: 0 15px 50px rgba(0,0,0,0.35);
        }
        .hero {
            background: linear-gradient(135deg, rgba(124,93,255,0.18), rgba(18,194,233,0.15));
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 1.4rem 1.6rem;
            margin-bottom: 1.2rem;
        }
        .metric-card {
            background: linear-gradient(145deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 14px;
            padding: 0.9rem 1rem;
        }
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            background: rgba(255,255,255,0.06);
            border-radius: 12px;
            padding: 10px 14px;
            color: var(--text);
        }
        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, var(--accent), var(--accent2));
            color: #0b0e17;
            font-weight: 700;
        }
        table { color: var(--text); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(page_title="Billboard x Kalshi Edge", layout="wide")
    _inject_css()
    st.markdown(
        """
        <div class="hero">
            <h1 style="margin-bottom:0.4rem;">Billboard #1 — Trading Edge</h1>
            <p style="color:#cbd1e2;margin-bottom:0;">Live Kalshi prices vs model probabilities. Hunt positive edge, act fast.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    model, feature_cols = load_model()
    if model is None:
        return
    metrics = load_metrics()

    with st.sidebar:
        st.header("Controls")
        default_event = os.getenv("KALSHI_EVENT_TICKER", "KXTOPSONG-25DEC20")
        event_ticker = st.text_input("Kalshi event ticker", value=default_event)
        top_k = st.slider("Rows to show", min_value=5, max_value=30, value=15, step=1)
        edge_threshold = st.slider(
            "Min edge to flag (probability points)",
            min_value=0.0,
            max_value=0.4,
            value=0.05,
            step=0.01,
        )
        st.caption(
            "Edge = model_prob - price_prob (Buy YES @ ask) or price_prob - model_prob (Sell YES @ bid)"
        )

    # Load latest features
    latest_itunes, latest_date = build_latest_feature_frame()
    # Ensure all feature columns exist for prediction
    for col in feature_cols:
        if col not in latest_itunes.columns:
            latest_itunes[col] = 0
    # Ensure song/artist columns exist for display
    if "song_name" not in latest_itunes.columns:
        latest_itunes[["song_name", "artist_name"]] = latest_itunes["key"].str.split(
            "||", expand=True, regex=False
        )
        latest_itunes["song_name"] = latest_itunes["song_name"].str.title()
        latest_itunes["artist_name"] = latest_itunes["artist_name"].str.title()
    if "artist_name" not in latest_itunes.columns:
        latest_itunes["artist_name"] = latest_itunes["artist_name"]

    apple_raw = load_apple()
    spotify_raw = load_spotify()
    youtube_raw = load_youtube()
    apple = latest_by_key(apple_raw, ["am_streams", "am_chart_position"]).set_index("key")
    spotify = latest_by_key(spotify_raw, ["sp_streams", "sp_chart_position"]).set_index("key")
    youtube = latest_by_key(youtube_raw, ["views"]).set_index("key")

    # Freshness indicators
    st.markdown("#### Data freshness")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("iTunes", str(latest_itunes["collection_date"].max().date()))
    c2.metric("Apple Music", str(apple_raw["collection_date"].max().date()) if not apple_raw.empty else "n/a")
    c3.metric("Spotify", str(spotify_raw["collection_date"].max().date()) if not spotify_raw.empty else "n/a")
    c4.metric("YouTube", str(youtube_raw["collection_date"].max().date()) if not youtube_raw.empty else "n/a")

    # Model predictions (iTunes)
    latest_itunes["prob_yes1"] = model.predict_proba(latest_itunes[feature_cols])[:, 1]
    latest_itunes = latest_itunes.sort_values("prob_yes1", ascending=False)

    # Kalshi markets + comparisons
    markets = render_kalshi(event_ticker)
    if markets:
        rows = []
        for m in markets:
            ticker = m.get("ticker")
            subtitle = m.get("subtitle", "")
            yes_bid = m.get("yes_bid")
            yes_ask = m.get("yes_ask")
            prob_bid = yes_bid / 100 if yes_bid is not None else None
            prob_ask = yes_ask / 100 if yes_ask is not None else None
            prob_mid = None
            if prob_bid is not None and prob_ask is not None:
                prob_mid = (prob_bid + prob_ask) / 2
            if "::" in subtitle:
                song, artist = subtitle.split("::", 1)
            else:
                song, artist = subtitle, ""
            key = _norm(song) + "||" + _norm(artist)
            base_prob = None
            if key in latest_itunes["key"].values:
                base_prob = latest_itunes.loc[latest_itunes["key"] == key, "prob_yes1"].max()
            boost = heuristic_boost(key, apple, spotify, youtube)
            final_prob = None if base_prob is None else min(1.0, base_prob + boost)

            ev_buy_yes = math.nan
            ev_sell_yes = math.nan
            if final_prob is not None and prob_ask is not None:
                ev_buy_yes = final_prob - prob_ask
            if final_prob is not None and prob_bid is not None:
                ev_sell_yes = prob_bid - final_prob

            best_action = ""
            best_ev = math.nan
            best_price = math.nan
            candidates = [
                ("Buy YES", ev_buy_yes, prob_ask),
                ("Sell YES", ev_sell_yes, prob_bid),
            ]
            for action, ev, price in candidates:
                if ev is not None and not math.isnan(ev):
                    if math.isnan(best_ev) or ev > best_ev:
                        best_ev = ev
                        best_action = action
                        best_price = price

            rows.append(
                {
                    "ticker": ticker,
                    "song": song.strip(),
                    "artist": artist.strip(),
                    "kalshi_bid_p": prob_bid,
                    "kalshi_ask_p": prob_ask,
                    "kalshi_mid_p": prob_mid,
                    "model_base_p": base_prob,
                    "boost": boost,
                    "model_final_p": final_prob,
                    "edge_mid": None if prob_mid is None or final_prob is None else final_prob - prob_mid,
                    "ev_buy_yes": ev_buy_yes,
                    "ev_sell_yes": ev_sell_yes,
                    "best_action": best_action,
                    "best_ev": best_ev,
                    "best_price_p": best_price,
                }
            )

        df = pd.DataFrame(rows)
        df = df.sort_values("best_ev", ascending=False, na_position="last")

        positive = df[
            ((df["ev_buy_yes"].notna()) & (df["ev_buy_yes"] >= edge_threshold))
            | ((df["ev_sell_yes"].notna()) & (df["ev_sell_yes"] >= edge_threshold))
        ]

        def _present(table: pd.DataFrame):
            display_cols = [
                "ticker",
                "song",
                "artist",
                "kalshi_bid_p",
                "kalshi_ask_p",
                "kalshi_mid_p",
                "model_final_p",
                "best_action",
                "best_price_p",
                "best_ev",
            ]
            present = table[display_cols].copy()
            percent_cols = ["kalshi_bid_p", "kalshi_ask_p", "kalshi_mid_p", "model_final_p", "best_price_p"]
            for col in percent_cols:
                present[col] = present[col].map(_fmt_pct)
            present["best_ev"] = present["best_ev"].map(_fmt_pct)
            present.rename(
                columns={
                    "kalshi_bid_p": "Bid",
                    "kalshi_ask_p": "Ask",
                    "kalshi_mid_p": "Mid",
                    "model_final_p": "Model",
                    "best_price_p": "Price",
                    "best_ev": "Edge",
                    "best_action": "Action",
                },
                inplace=True,
            )
            return present

        # Hero metrics for markets
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("Markets loaded", f"{len(df)}")
        col_b.metric("Flagged trades", f"{len(positive)}")
        col_c.metric("Top edge", _fmt_pct(df["best_ev"].max() if not df.empty else math.nan))
        col_d.metric("Latest iTunes", str(latest_date.date()))

        if metrics:
            st.markdown("##### Model validation (time-based split)")
            m_tr = metrics.get("train", {})
            m_val = metrics.get("val", {})
            m_te = metrics.get("test", {})
            threshold = metrics.get("threshold", None)
            mt1, mt2, mt3 = st.columns(3)
            mt1.metric("Train AUC", f"{m_tr.get('roc_auc', float('nan')):.3f}")
            mt2.metric("Val AUC", f"{m_val.get('roc_auc', float('nan')):.3f}")
            test_acc = m_te.get("accuracy", float("nan"))
            mt3.metric("Test Accuracy", f"{test_acc*100:.1f}%" if not math.isnan(test_acc) else "—")
            if threshold is not None:
                st.caption(f"Decision threshold (max F1 on val, floored): {threshold:.3f}")
            # Friendly summary text
            pos_caught = m_te.get("confusion", {}).get("tp", 0) if m_te else 0
            pos_total = (m_te.get("confusion", {}).get("tp", 0) + m_te.get("confusion", {}).get("fn", 0)) if m_te else 0
            st.caption(
                f"Test snapshot: {pos_caught}/{pos_total} positives caught; model favors precision over recall on sparse positives. "
                "Use as a ranking signal; sanity-check edges before trading."
            )

        tab_overview, tab_markets, tab_sources = st.tabs(["Overview", "Markets", "Sources"])

        with tab_overview:
            st.markdown("##### Top Candidates (model view)")
            show_cols = ["song_name", "artist_name", "digital_sales", "sales_ma7", "sales_ma14", "prob_yes1"]
            for c in show_cols:
                if c not in latest_itunes.columns:
                    latest_itunes[c] = None
            top_df = (
                latest_itunes[show_cols]
                .head(top_k)
                .rename(columns={"prob_yes1": "prob_hit_#1"})
                .copy()
            )
            top_df["prob_hit_#1"] = top_df["prob_hit_#1"].map(_fmt_pct)
            st.dataframe(top_df, height=420, width="stretch")

            # Chart: top edges (model vs mid)
            edge_chart_df = df.dropna(subset=["kalshi_mid_p", "model_final_p"]).head(top_k)
            if not edge_chart_df.empty:
                chart = (
                    alt.Chart(edge_chart_df)
                    .transform_fold(
                        fold=["model_final_p", "kalshi_mid_p"],
                        as_=["series", "prob"],
                    )
                    .transform_calculate(
                        series_label="datum.series == 'model_final_p' ? 'Model' : 'Kalshi mid'"
                    )
                    .mark_bar(opacity=0.85)
                    .encode(
                        x=alt.X("ticker:N", sort="-y", title="Ticker"),
                        y=alt.Y("prob:Q", title="Probability", axis=alt.Axis(format="%")),
                        color=alt.Color(
                            "series_label:N",
                            scale=alt.Scale(domain=["Model", "Kalshi mid"], range=["#7c5dff", "#12c2e9"]),
                            legend=alt.Legend(title=""),
                        ),
                        tooltip=[
                            alt.Tooltip("ticker:N", title="Ticker"),
                            alt.Tooltip("series_label:N", title="Series"),
                            alt.Tooltip("prob:Q", format=".1%", title="Probability"),
                        ],
                    )
                    .properties(height=320)
                )
                st.altair_chart(chart, use_container_width=True)

        with tab_markets:
            st.markdown(f"##### Flagged trades (edge ≥ {edge_threshold:.0%})")
            if positive.empty:
                st.info("No markets meet the edge threshold yet.")
            else:
                st.dataframe(_present(positive), height=420, width="stretch")

            st.markdown("##### All markets (sorted by best EV)")
            st.dataframe(_present(df), height=520, width="stretch")

            scatter_df = df.dropna(subset=["kalshi_mid_p", "model_final_p"])
            if not scatter_df.empty:
                scatter = (
                    alt.Chart(scatter_df)
                    .mark_circle(size=120, opacity=0.65)
                    .encode(
                        x=alt.X("kalshi_mid_p:Q", title="Kalshi mid prob"),
                        y=alt.Y("model_final_p:Q", title="Model prob"),
                        color=alt.Color("best_ev:Q", scale=alt.Scale(scheme="tealblues"), title="Edge"),
                        tooltip=["ticker", "song", "artist", "best_action", "best_ev"],
                    )
                    .properties(height=420)
                )
                st.altair_chart(scatter, use_container_width=True)

        with tab_sources:
            st.markdown("##### Data freshness")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("iTunes", str(latest_itunes["collection_date"].max().date()))
            c2.metric("Apple Music", str(apple_raw["collection_date"].max().date()) if not apple_raw.empty else "n/a")
            c3.metric("Spotify", str(spotify_raw["collection_date"].max().date()) if not spotify_raw.empty else "n/a")
            c4.metric("YouTube", str(youtube_raw["collection_date"].max().date()) if not youtube_raw.empty else "n/a")

    # Orderbook intentionally omitted


if __name__ == "__main__":
    main()
