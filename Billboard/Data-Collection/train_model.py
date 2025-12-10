"""
Baseline ML training script for Billboard #1 prediction.
- Uses iTunes sales + Spotify/Apple Music streaming + YouTube views (kworb)
- Labels: Billboard historical CSV (reached_number_1)
Outputs:
  models/billboard_rf.pkl (model)
  models/feature_columns.json (feature order)
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    precision_recall_fscore_support,
    accuracy_score,
    precision_recall_curve,
    auc as sk_auc,
)
from sklearn.utils import resample

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)
METRICS_PATH = MODELS_DIR / "training_metrics.json"


def _norm(text: str) -> str:
    """
    Robust normalization: lowercase, unicode fold, replace & with 'and',
    remove punctuation, collapse whitespace.
    """
    if text is None:
        return ""
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("&", "and")
    text = re.sub(r"[^a-z0-9\\s]", " ", text)
    text = re.sub(r"\\s+", " ", text).strip()
    return text


def load_itunes(data_dir: Path = DATA_DIR / "itunes") -> pd.DataFrame:
    files = sorted(data_dir.glob("itunes_*.csv"))
    if not files:
        raise FileNotFoundError(f"No iTunes CSVs found in {data_dir}")
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df["collection_date"] = pd.to_datetime(df["collection_date"])
        dfs.append(df)
    itunes = pd.concat(dfs, ignore_index=True)
    for col in ["digital_sales", "total_sales"]:
        itunes[col] = pd.to_numeric(itunes[col], errors="coerce").fillna(0)
    itunes["key"] = itunes["song_name"].apply(_norm) + "||" + itunes["artist_name"].apply(_norm)
    return itunes.groupby(["key", "collection_date"], as_index=False).agg(
        digital_sales=("digital_sales", "sum"),
        total_sales=("total_sales", "sum"),
    )


def add_itunes_features(itunes: pd.DataFrame) -> pd.DataFrame:
    itunes = itunes.sort_values(["key", "collection_date"])
    g = itunes.groupby("key")
    itunes["sales_ma7"] = g["digital_sales"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    itunes["sales_ma14"] = g["digital_sales"].transform(lambda s: s.rolling(14, min_periods=1).mean())
    itunes["sales_delta1"] = g["digital_sales"].diff()
    itunes["sales_delta7"] = g["digital_sales"].diff(7)
    itunes["sales_momentum"] = itunes["sales_ma7"] / (itunes["sales_ma14"].replace(0, np.nan))
    itunes["sales_momentum"] = itunes["sales_momentum"].fillna(0)
    return itunes


def load_billboard(billboard_path: Path = DATA_DIR / "billboard_historical_processed.csv") -> pd.DataFrame:
    if not billboard_path.exists():
        raise FileNotFoundError(f"Billboard file not found: {billboard_path}")
    bb = pd.read_csv(billboard_path)
    # Normalize column names
    if "chart_date" in bb.columns:
        bb["chart_date"] = pd.to_datetime(bb["chart_date"])
    if "song_name" not in bb.columns and "song" in bb.columns:
        bb = bb.rename(columns={"song": "song_name"})
    if "artist_name" not in bb.columns and "performer" in bb.columns:
        bb = bb.rename(columns={"performer": "artist_name"})
    if "reached_number_1" not in bb.columns and "chart_position" in bb.columns:
        bb["reached_number_1"] = (bb["chart_position"] == 1).astype(int)
    bb["key"] = bb["song_name"].apply(_norm) + "||" + bb["artist_name"].apply(_norm)
    return bb


def load_spotify(data_dir: Path = DATA_DIR / "spotify") -> pd.DataFrame:
    files = sorted(data_dir.glob("spotify_*.csv"))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df["collection_date"] = pd.to_datetime(df["collection_date"])
        df["streams"] = pd.to_numeric(df["streams"], errors="coerce").fillna(0)
        df["chart_position"] = pd.to_numeric(df.get("chart_position", 0), errors="coerce").fillna(0)
        df["key"] = df["song_name"].apply(_norm) + "||" + df["artist_name"].apply(_norm)
        dfs.append(df[["key", "streams", "chart_position", "collection_date"]])
    sp = pd.concat(dfs, ignore_index=True)
    sp = sp.groupby(["key", "collection_date"], as_index=False).agg(
        sp_streams=("streams", "sum"),
        sp_chart_position=("chart_position", "min"),
    )
    return sp


def add_spotify_features(sp: pd.DataFrame) -> pd.DataFrame:
    if sp.empty:
        return sp
    sp = sp.sort_values(["key", "collection_date"])
    g = sp.groupby("key")
    sp["sp_ma7"] = g["sp_streams"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    sp["sp_ma14"] = g["sp_streams"].transform(lambda s: s.rolling(14, min_periods=1).mean())
    sp["sp_delta1"] = g["sp_streams"].diff()
    sp["sp_delta7"] = g["sp_streams"].diff(7)
    sp["sp_momentum"] = sp["sp_ma7"] / (sp["sp_ma14"].replace(0, np.nan))
    sp["sp_momentum"] = sp["sp_momentum"].fillna(0)
    return sp


def load_apple(data_dir: Path = DATA_DIR / "apple_music") -> pd.DataFrame:
    files = sorted(data_dir.glob("apple_music_*.csv"))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df["collection_date"] = pd.to_datetime(df["collection_date"])
        df["streams"] = pd.to_numeric(df["streams"], errors="coerce").fillna(0)
        df["chart_position"] = pd.to_numeric(df.get("chart_position", 0), errors="coerce").fillna(0)
        df["key"] = df["song_name"].apply(_norm) + "||" + df["artist_name"].apply(_norm)
        dfs.append(df[["key", "streams", "chart_position", "collection_date"]])
    am = pd.concat(dfs, ignore_index=True)
    am = am.groupby(["key", "collection_date"], as_index=False).agg(
        am_streams=("streams", "sum"),
        am_chart_position=("chart_position", "min"),
    )
    return am


def add_apple_features(am: pd.DataFrame) -> pd.DataFrame:
    if am.empty:
        return am
    am = am.sort_values(["key", "collection_date"])
    g = am.groupby("key")
    am["am_ma7"] = g["am_streams"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    am["am_ma14"] = g["am_streams"].transform(lambda s: s.rolling(14, min_periods=1).mean())
    am["am_delta1"] = g["am_streams"].diff()
    am["am_delta7"] = g["am_streams"].diff(7)
    am["am_momentum"] = am["am_ma7"] / (am["am_ma14"].replace(0, np.nan))
    am["am_momentum"] = am["am_momentum"].fillna(0)
    return am


def load_youtube(data_dir: Path = DATA_DIR / "youtube") -> pd.DataFrame:
    files = sorted(data_dir.glob("youtube_*.csv"))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df["collection_date"] = pd.to_datetime(df["collection_date"])
        df["views"] = pd.to_numeric(df["views"], errors="coerce").fillna(0)
        df["key"] = df["song_name"].apply(_norm) + "||" + df["artist_name"].apply(_norm)
        dfs.append(df[["key", "views", "collection_date"]])
    yt = pd.concat(dfs, ignore_index=True)
    yt = yt.groupby(["key", "collection_date"], as_index=False).agg(views=("views", "sum"))
    return yt


def add_youtube_features(yt: pd.DataFrame) -> pd.DataFrame:
    if yt.empty:
        return yt
    yt = yt.sort_values(["key", "collection_date"])
    g = yt.groupby("key")
    yt["yt_ma7"] = g["views"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    yt["yt_ma14"] = g["views"].transform(lambda s: s.rolling(14, min_periods=1).mean())
    yt["yt_delta1"] = g["views"].diff()
    yt["yt_delta7"] = g["views"].diff(7)
    yt["yt_momentum"] = yt["yt_ma7"] / (yt["yt_ma14"].replace(0, np.nan))
    yt["yt_momentum"] = yt["yt_momentum"].fillna(0)
    return yt


def build_dataset(itunes: pd.DataFrame, bb: pd.DataFrame) -> pd.DataFrame:
    bb = bb.copy()
    bb["feature_date"] = bb["chart_date"] - timedelta(days=7)

    # Load other sources (core training uses iTunes; Apple optional; sp/yt optional)
    sp = add_spotify_features(load_spotify())
    am = add_apple_features(load_apple())
    yt = add_youtube_features(load_youtube())

    # Align to iTunes start (widest coverage). Do not restrict to Apple start.
    min_date = itunes["collection_date"].min()
    bb = bb[bb["feature_date"] >= min_date]

    merged = bb.merge(
        itunes,
        left_on=["key", "feature_date"],
        right_on=["key", "collection_date"],
        how="left",
        suffixes=("", "_it"),
    )
    # Merge core (iTunes + Apple). Keep sp/yt merges optional if coverage exists.
    merged = bb.merge(
        itunes,
        left_on=["key", "feature_date"],
        right_on=["key", "collection_date"],
        how="left",
        suffixes=("", "_it"),
    )
    merged = merged.merge(
        am,
        left_on=["key", "feature_date"],
        right_on=["key", "collection_date"],
        how="left",
        suffixes=("", "_am"),
    )
    if not sp.empty:
        merged = merged.merge(
            sp,
            left_on=["key", "feature_date"],
            right_on=["key", "collection_date"],
            how="left",
            suffixes=("", "_sp"),
        )
    if not yt.empty:
        merged = merged.merge(
            yt,
            left_on=["key", "feature_date"],
            right_on=["key", "collection_date"],
            how="left",
            suffixes=("", "_yt"),
        )

    # Core feature set: iTunes + Apple + Spotify + YouTube if present
    feature_cols = [
        # iTunes
        "digital_sales",
        "total_sales",
        "sales_ma7",
        "sales_ma14",
        "sales_delta1",
        "sales_delta7",
        "sales_momentum",
        # Apple
        "am_streams",
        "am_chart_position",
        "am_ma7",
        "am_ma14",
        "am_delta1",
        "am_delta7",
        "am_momentum",
        # Spotify
        "sp_streams",
        "sp_chart_position",
        "sp_ma7",
        "sp_ma14",
        "sp_delta1",
        "sp_delta7",
        "sp_momentum",
        # YouTube
        "views",
        "yt_ma7",
        "yt_ma14",
        "yt_delta1",
        "yt_delta7",
        "yt_momentum",
    ]

    # Ensure all feature columns exist
    for col in feature_cols:
        if col not in merged.columns:
            merged[col] = 0

    # Fill missing numeric features with 0
    merged[feature_cols] = merged[feature_cols].fillna(0)
    merged = merged.replace([np.inf, -np.inf], 0)

    # Drop rows where all features are zero (no coverage)
    feat_mat = merged[feature_cols].to_numpy()
    keep_mask = (feat_mat.sum(axis=1) != 0)
    merged = merged.loc[keep_mask]

    merged = merged.sort_values("chart_date")
    return merged, feature_cols


def time_split(df: pd.DataFrame, train_ratio: float = 0.8):
    cutoff_idx = int(len(df) * train_ratio)
    train = df.iloc[:cutoff_idx]
    test = df.iloc[cutoff_idx:]
    return train, test


def nested_time_split(df: pd.DataFrame, train_ratio: float = 0.7, val_ratio: float = 0.15):
    """Split into train/val/test preserving time order."""
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    train = df.iloc[:train_end]
    val = df.iloc[train_end:val_end]
    test = df.iloc[val_end:]
    return train, val, test


def train():
    itunes = load_itunes()
    itunes = add_itunes_features(itunes)
    bb = load_billboard()
    merged, feature_cols = build_dataset(itunes, bb)

    # Nested split: train/val/test by time
    train_df, val_df, test_df = nested_time_split(merged, train_ratio=0.7, val_ratio=0.15)
    X_train, y_train = train_df[feature_cols], train_df["reached_number_1"]
    X_val, y_val = val_df[feature_cols], val_df["reached_number_1"]
    X_test, y_test = test_df[feature_cols], test_df["reached_number_1"]

    # Upsample positives in train to balance
    train_pos = train_df[train_df["reached_number_1"] == 1]
    train_neg = train_df[train_df["reached_number_1"] == 0]
    if not train_pos.empty:
        train_pos_up = resample(train_pos, replace=True, n_samples=len(train_neg), random_state=42)
        train_bal = pd.concat([train_neg, train_pos_up]).sort_values("chart_date")
    else:
        train_bal = train_df
    X_train_bal, y_train_bal = train_bal[feature_cols], train_bal["reached_number_1"]

    base_model = RandomForestClassifier(
        n_estimators=600,
        max_depth=6,
        min_samples_leaf=3,
        max_features="sqrt",
        random_state=42,
        class_weight="balanced",
        n_jobs=-1,
    )
    base_model.fit(X_train_bal, y_train_bal)
    # Calibrate to improve probability quality under imbalance
    model = CalibratedClassifierCV(base_model, method="isotonic", cv=3)
    model.fit(X_train_bal, y_train_bal)

    def _collect_metrics(split: str, y_true, y_prob, threshold: float = 0.5):
        y_pred = (y_prob >= threshold).astype(int)
        acc = accuracy_score(y_true, y_pred)
        auc = roc_auc_score(y_true, y_prob)
        precision, recall, f1, support = precision_recall_fscore_support(
            y_true, y_pred, labels=[0, 1], zero_division=0
        )
        pos_support = int(support[1])
        neg_support = int(support[0])
        prevalence = float(pos_support) / float(pos_support + neg_support) if (pos_support + neg_support) else 0.0
        predicted_pos_rate = float((y_pred == 1).mean())
        return {
            "split": split,
            "threshold": threshold,
            "accuracy": acc,
            "roc_auc": auc,
            "precision_pos": precision[1],
            "recall_pos": recall[1],
            "f1_pos": f1[1],
            "support_pos": pos_support,
            "support_neg": neg_support,
            "prevalence": prevalence,
            "predicted_positive_rate": predicted_pos_rate,
        }

    y_prob_train = model.predict_proba(X_train)[:, 1]
    y_prob_val = model.predict_proba(X_val)[:, 1]
    y_prob_test = model.predict_proba(X_test)[:, 1]

    def _best_threshold(y_true, prob):
        prec, rec, thr = precision_recall_curve(y_true, prob)
        f1 = (2 * prec * rec) / (prec + rec + 1e-9)
        best_idx = int(np.nanargmax(f1))
        return float(thr[best_idx]) if best_idx < len(thr) else 0.5

    best_thr = _best_threshold(y_val, y_prob_val)
    # Presentable/recall-friendly floor so we don't choke on sparse positives
    best_thr = max(best_thr, 0.1)

    def _confusion(y_true, prob, threshold):
        y_pred = (prob >= threshold).astype(int)
        tp = int(((y_true == 1) & (y_pred == 1)).sum())
        fp = int(((y_true == 0) & (y_pred == 1)).sum())
        fn = int(((y_true == 1) & (y_pred == 0)).sum())
        tn = int(((y_true == 0) & (y_pred == 0)).sum())
        return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}

    def _pr_auc(y_true, prob):
        prec, rec, _ = precision_recall_curve(y_true, prob)
        return float(sk_auc(rec, prec))

    metrics_train = _collect_metrics("train", y_train, y_prob_train, threshold=best_thr)
    metrics_val = _collect_metrics("val", y_val, y_prob_val, threshold=best_thr)
    metrics_test = _collect_metrics("test", y_test, y_prob_test, threshold=best_thr)
    metrics_train["pr_auc"] = _pr_auc(y_train, y_prob_train)
    metrics_val["pr_auc"] = _pr_auc(y_val, y_prob_val)
    metrics_test["pr_auc"] = _pr_auc(y_test, y_prob_test)
    metrics_train["confusion"] = _confusion(y_train, y_prob_train, best_thr)
    metrics_val["confusion"] = _confusion(y_val, y_prob_val, best_thr)
    metrics_test["confusion"] = _confusion(y_test, y_prob_test, best_thr)

    print("=" * 80)
    print("MODEL EVALUATION (time-based split)")
    print("=" * 80)
    print(f"Train: acc={metrics_train['accuracy']:.3f}, auc={metrics_train['roc_auc']:.3f}, "
          f"precision_pos={metrics_train['precision_pos']:.3f}, recall_pos={metrics_train['recall_pos']:.3f}")
    print(f"Val  : acc={metrics_val['accuracy']:.3f}, auc={metrics_val['roc_auc']:.3f}, "
          f"precision_pos={metrics_val['precision_pos']:.3f}, recall_pos={metrics_val['recall_pos']:.3f}")
    print(f"Test : acc={metrics_test['accuracy']:.3f}, auc={metrics_test['roc_auc']:.3f}, "
          f"precision_pos={metrics_test['precision_pos']:.3f}, recall_pos={metrics_test['recall_pos']:.3f}")
    print(f"\nThreshold selected (max F1 on val, floored at 0.1): {best_thr:.3f}")
    print("\nClassification report (test, threshold=best):")
    print(classification_report(y_test, (y_prob_test >= best_thr).astype(int), digits=3))
    print("Top feature importances (base RF):")
    importances = sorted(zip(base_model.feature_importances_, feature_cols), reverse=True)
    for imp, name in importances:
        print(f"  {name}: {imp:.4f}")

    # Save artifacts
    model_path = MODELS_DIR / "billboard_rf.pkl"
    joblib.dump(model, model_path)
    with open(MODELS_DIR / "feature_columns.json", "w") as f:
        json.dump(feature_cols, f, indent=2)
    with open(METRICS_PATH, "w") as f:
        json.dump({"train": metrics_train, "val": metrics_val, "test": metrics_test, "threshold": best_thr}, f, indent=2)

    print(f"\nModel saved to {model_path}")
    print(f"Feature list saved to {MODELS_DIR / 'feature_columns.json'}")
    print(f"Metrics saved to {METRICS_PATH}")


if __name__ == "__main__":
    train()

