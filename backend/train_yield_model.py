"""
train_yield_model.py — Dedicated yield prediction model training script.

Uses a separate richer dataset with additional yield-specific features:
  - irrigation_type (Rainfed/Canal/Drip/Flood/Sprinkler)
  - soil_type (Black/Alluvial/Sandy/Loamy/Clayey)
  - year (2010–2023 normalized)

These features dramatically improve yield R² compared to the crop dataset.

Dataset: notebooks/Yield_Dataset_V1.csv

Artefacts saved to backend/models/:
  yield_model.pkl        — RandomForestRegressor (replaces old one)
  scaler_yield.pkl       — StandardScaler for yield features
  label_encoder_yield.pkl— LabelEncoder for crop names (yield model)
  feature_cols_yield.pkl — yield feature column list

Expected yield R²: ≥ 0.65

Usage:
    cd backend
    python train_yield_model.py
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

RANDOM_SEED          = 42
MIN_SAMPLES_PER_CROP = 100
MAX_SAMPLES_PER_CROP = 1000
OUTLIER_SIGMA        = 2.5

# Crops to drop — too few samples or poor yield signal
DROP_CROPS = {
    "APPLE", "ORANGE", "WATERMELON",
    "JUTE", "KIDNEYBEANS", "COCONUT",
    "POMEGRANATE", "CHILLIES",
    "PIGEONPEAS", "SUNFLOWER",
}

# ─── Dataset location ────────────────────────────────────────────────────────
_BACKEND_DIR  = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT    = os.path.dirname(_BACKEND_DIR)
_DATASET_PATH = os.path.join(
    _REPO_ROOT, "notebooks", "Yield_Dataset_V1.csv"
)

_LABEL_COL = "label"
_YIELD_COL = "yield"

# ── Yield model features — richer than crop model ────────────────────────────
_BASE_FEATURES = [
    "nitrogen", "phosphorus", "potassium",
    "temperature", "humidity",
    "ph", "rainfall",
    "district", "season", "area",
    "irrigation_type",    # ← new
    "soil_type",          # ← new
    "year",               # ← new
]

_ENGINEERED_FEATURES = [
    "NPK_total",
    "NPK_ratio",
    "Climate_score",
    "Temp_humidity_interaction",
    "Soil_quality_score",
    "rain_per_temp",      # ← new
    "N_to_P_ratio",       # ← new
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["NPK_total"]                 = df["nitrogen"] + df["phosphorus"] + df["potassium"]
    df["NPK_ratio"]                 = df["nitrogen"] / (df["phosphorus"] + df["potassium"] + 1e-6)
    df["Climate_score"]             = 0.5 * df["temperature"] + 0.5 * (df["rainfall"] / 100.0)
    df["Temp_humidity_interaction"] = df["temperature"] * df["humidity"]
    df["Soil_quality_score"]        = 10.0 * np.exp(-0.5 * ((df["ph"] - 6.5) / 0.8) ** 2)
    df["rain_per_temp"]             = df["rainfall"] / (df["temperature"] + 1e-6)
    df["N_to_P_ratio"]              = df["nitrogen"] / (df["phosphorus"] + 1e-6)
    return df


def _clean_dataset(df: pd.DataFrame) -> pd.DataFrame:

    # Step 1: Drop explicit crops
    n_before = len(df)
    df = df[~df[_LABEL_COL].isin(DROP_CROPS)].reset_index(drop=True)
    print(f"[clean] Dropped {len(DROP_CROPS)} explicit crops ({n_before - len(df):,} rows removed)")

    # Step 2: Drop rare crops
    counts        = df[_LABEL_COL].value_counts()
    valid_crops   = counts[counts >= MIN_SAMPLES_PER_CROP].index
    removed_crops = sorted(set(counts.index) - set(valid_crops))
    n_before      = len(df)
    df = df[df[_LABEL_COL].isin(valid_crops)].reset_index(drop=True)
    if removed_crops:
        print(f"[clean] Dropped rare crops: {removed_crops} ({n_before - len(df):,} rows removed)")

    # Step 3: Remove yield outliers
    keep_mask = pd.Series(True, index=df.index)
    for _, group in df.groupby(_LABEL_COL):
        std_y = group[_YIELD_COL].std()
        if std_y > 0:
            outlier_mask = (
                (group[_YIELD_COL] - group[_YIELD_COL].mean()).abs()
                > OUTLIER_SIGMA * std_y
            )
            keep_mask.loc[group.index[outlier_mask]] = False
    n_before = len(df)
    df       = df[keep_mask].reset_index(drop=True)
    print(f"[clean] Removed {n_before - len(df):,} yield outliers.")

    # Step 4: Balance
    parts = []
    for _, group in df.groupby(_LABEL_COL):
        if len(group) > MAX_SAMPLES_PER_CROP:
            parts.append(group.sample(n=MAX_SAMPLES_PER_CROP, random_state=RANDOM_SEED))
        else:
            parts.append(group)
    df = (
        pd.concat(parts, ignore_index=True)
        .sample(frac=1, random_state=RANDOM_SEED)
        .reset_index(drop=True)
    )
    print(f"[clean] After balancing: {len(df):,} rows, {df[_LABEL_COL].nunique()} crops.")
    return df


# ─── Training ─────────────────────────────────────────────────────────────────

def train_and_save() -> None:

    # ── Load ─────────────────────────────────────────────────────────────────
    if not os.path.exists(_DATASET_PATH):
        raise FileNotFoundError(
            f"Dataset not found: {_DATASET_PATH!r}\n"
            "Ensure 'Yield_Dataset_V1.csv' is in notebooks/ directory."
        )
    df = pd.read_csv(_DATASET_PATH)
    print(f"[load] {_DATASET_PATH}")
    print(f"       shape={df.shape}  crops={df[_LABEL_COL].nunique()}")

    # ── Verify required columns ───────────────────────────────────────────────
    required = ["irrigation_type", "soil_type", "year", "humidity"]
    missing  = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}. Use Yield_Dataset_V1.csv")
    print(f"[verify] New columns present: irrigation_type, soil_type, year ✓")

    # ── Clean ─────────────────────────────────────────────────────────────────
    df = _clean_dataset(df)

    # ── Engineered features ───────────────────────────────────────────────────
    df = _add_engineered_features(df)

    # ── Verify all features exist ─────────────────────────────────────────────
    all_features = _BASE_FEATURES + _ENGINEERED_FEATURES
    missing_f = [f for f in all_features if f not in df.columns]
    if missing_f:
        raise ValueError(f"Missing feature columns: {missing_f}")
    print(f"[verify] All {len(all_features)} yield features present ✓")

    # ── Encode crop labels ────────────────────────────────────────────────────
    le = LabelEncoder()
    df["crop_encoded"] = le.fit_transform(df[_LABEL_COL].values)
    print(f"\nCrop classes ({len(le.classes_)}): {list(le.classes_)}")

    # ── Build feature matrix ──────────────────────────────────────────────────
    feature_cols_yield = all_features + ["crop_encoded"]
    X_yield = df[feature_cols_yield].values

    # Clip extreme yield values (top 1%)
    y_yield = df[_YIELD_COL].values
    y_yield = np.clip(y_yield, 0, np.percentile(y_yield, 99))

    # ── Train / test split ────────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X_yield, y_yield,
        test_size=0.20, random_state=RANDOM_SEED,
    )
    print(f"\nTrain size: {len(X_train):,} | Test size: {len(X_test):,}")
    print(f"Yield features ({len(feature_cols_yield)}): {feature_cols_yield}")

    # =========================================================================
    # Yield Model — with regularization to prevent overfitting
    # =========================================================================
    print("\n" + "=" * 68)
    print("  Training Yield Prediction Model")
    print("=" * 68)

    scaler    = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    yield_model = RandomForestRegressor(
        n_estimators=500,
        max_depth=15,          # regularized to prevent overfitting
        min_samples_leaf=10,   # regularized
        min_samples_split=20,  # regularized
        max_features="sqrt",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    yield_model.fit(X_train_sc, y_train)

    for split_lbl, X_s, y_s in [
        ("Train", X_train_sc, y_train),
        ("Test ", X_test_sc,  y_test),
    ]:
        y_pred = yield_model.predict(X_s)
        r2   = r2_score(y_s, y_pred)
        mae  = mean_absolute_error(y_s, y_pred)
        rmse = float(np.sqrt(mean_squared_error(y_s, y_pred)))
        print(f"  {split_lbl}  R²={r2:.4f}  MAE={mae:.4f}  RMSE={rmse:.4f}")

    # CV
    cv_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("reg", RandomForestRegressor(
            n_estimators=500, max_depth=15,
            min_samples_leaf=10, min_samples_split=20,
            max_features="sqrt", random_state=RANDOM_SEED, n_jobs=-1,
        )),
    ])
    cv_scores = cross_val_score(
        cv_pipeline, X_yield, y_yield, cv=5, scoring="r2", n_jobs=-1,
    )
    print(f"  5-Fold CV R²: {cv_scores.round(4)} → mean={cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # Feature importance
    importances = yield_model.feature_importances_
    feat_imp = sorted(zip(feature_cols_yield, importances), key=lambda x: x[1], reverse=True)
    print("\n  Top 10 Feature Importances:")
    for feat, imp in feat_imp[:10]:
        print(f"    {feat:<35} {imp:.4f}")

    # ── Save artefacts ────────────────────────────────────────────────────────
    models_dir = os.path.join(_BACKEND_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)

    artefacts = {
        "yield_model.pkl":         yield_model,
        "scaler_yield.pkl":        scaler,
        "label_encoder_yield.pkl": le,
        "feature_cols_yield.pkl":  feature_cols_yield,
    }
    for filename, obj in artefacts.items():
        out_path = os.path.join(models_dir, filename)
        joblib.dump(obj, out_path)
        print(f"Saved: {out_path}")

    # Save yield metadata
    yield_meta = {
        "dataset":           os.path.join("notebooks", "Yield_Dataset_V1.csv"),
        "n_classes":         int(len(le.classes_)),
        "crop_classes":      list(le.classes_),
        "feature_names":     feature_cols_yield,
        "cv_r2_mean":        round(float(cv_scores.mean()), 4),
        "cv_r2_std":         round(float(cv_scores.std()), 4),
        "new_features":      ["irrigation_type", "soil_type", "year"],
        "random_seed":       RANDOM_SEED,
    }
    meta_path = os.path.join(models_dir, "yield_metadata.json")
    with open(meta_path, "w") as fh:
        json.dump(yield_meta, fh, indent=2)
    print(f"Saved: {meta_path}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 68)
    print("  YIELD TRAINING COMPLETE — SUMMARY")
    print("=" * 68)
    print(f"  Dataset        : {_DATASET_PATH}")
    print(f"  Rows used      : {len(df):,}")
    print(f"  Crop classes   : {len(le.classes_)}")
    print(f"  Yield features : {len(feature_cols_yield)}")
    print(f"  New features   : irrigation_type, soil_type, year")
    print(f"  5-Fold CV R²   : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    if cv_scores.mean() >= 0.65:
        print("  ✓ Yield R² target (≥ 0.65) MET")
    elif cv_scores.mean() >= 0.50:
        print("  ~ Yield R² improved — aim for 0.65+")
    else:
        print("  ✗ Yield R² target NOT MET")
    print("=" * 68)


if __name__ == "__main__":
    train_and_save()