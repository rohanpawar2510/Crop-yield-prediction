"""
train_models_final.py — Optimized model training for maximum accuracy.

Improvements over train_models_improved.py
------------------------------------------
* Uses the aggressively cleaned dataset (Crop_recommendation_final.csv)
  produced by scripts/ultimate_data_cleaner.py.
* Tighter Random Forest hyperparameters:
    - n_estimators  : 500  (vs 300)
    - max_depth     : 12   (optimal bias/variance balance)
    - min_samples_leaf : 8  (vs 5 — reduces overfitting)
    - min_samples_split: 15 (vs 10 — more stable splits)
* StandardScaler applied to all features.
* class_weight='balanced' for the crop classifier.
* 5-fold stratified cross-validation with detailed metrics.
* Tracks accuracy, F1, R², MAE and RMSE.
* Saves final model artefacts alongside originals.

Usage
-----
    cd backend
    python train_models_final.py

    # Or from the repository root:
    python backend/train_models_final.py
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_BACKEND_DIR)

# Primary dataset: new cleaned dataset (highest priority — use when available)
_CLEANED_DATASET = os.path.join(_REPO_ROOT, "notebooks", "crop_cleaned.csv")
# Fallback dataset: aggressively cleaned by ultimate_data_cleaner.py
_FINAL_DATASET = os.path.join(_REPO_ROOT, "notebooks", "Crop_recommendation_final.csv")
# Fallback chain: improved → single authoritative source dataset
_IMPROVED_DATASET = os.path.join(_REPO_ROOT, "notebooks", "Crop_recommendation_improved.csv")
_FALLBACK_DATASET = os.path.join(_REPO_ROOT, "notebooks", "Crop_Final_Updated (1).csv")

# Add scripts/ to path so feature_engineering is importable
_SCRIPTS_DIR = os.path.join(_REPO_ROOT, "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# Feature columns
# ---------------------------------------------------------------------------
_BASE_FEATURES = [
    "nitrogen", "phosphorus", "potassium",
    "temperature", "humidity", "ph", "rainfall",
]
_ENGINEERED_FEATURES = [
    "NPK_total",
    "NPK_ratio",
    "Climate_score",
    "Temp_humidity_interaction",
    "Soil_quality_score",
]
_LABEL_COL = "label"
_YIELD_COL = "yield"

# Optimised Random Forest hyperparameters
_RF_PARAMS: dict = dict(
    n_estimators=500,
    max_depth=12,
    min_samples_leaf=8,
    min_samples_split=15,
    max_features="sqrt",
    random_state=RANDOM_SEED,
    n_jobs=-1,
)


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def _pick_dataset() -> str:
    for path, label in [
        (_CLEANED_DATASET,  "cleaned"),
        (_FINAL_DATASET,    "final (ultimate-cleaned)"),
        (_IMPROVED_DATASET, "improved"),
        (_FALLBACK_DATASET, "standard"),
    ]:
        if os.path.exists(path):
            return path, label
    return _FALLBACK_DATASET, "standard"


def _load_dataset(path: str, label: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found at {path!r}.\n"
            "Run scripts/ultimate_data_cleaner.py first, or provide an "
            "alternative dataset."
        )
    df = pd.read_csv(path)
    print(f"[load] Using {label} dataset: {path}")
    print(f"       shape={df.shape}  crops={df[_LABEL_COL].nunique()}")
    null_count = int(df.isnull().sum().sum())
    if null_count:
        print(f"       ⚠  {null_count} null values found — will be dropped.")
    else:
        print("       ✓  No null values.")
    return df


def _ensure_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute engineered features if they are not already in the DataFrame."""
    missing = [c for c in _ENGINEERED_FEATURES if c not in df.columns]
    if not missing:
        return df
    print("[features] Engineered columns not found — computing now…")
    try:
        from feature_engineering import add_features
        df = add_features(df)
        print(f"[features] Added: {_ENGINEERED_FEATURES}")
    except ImportError:
        print(
            "[features] WARNING: feature_engineering module not available. "
            "Engineered features will be skipped."
        )
    return df


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_and_save() -> None:
    # ── Load ─────────────────────────────────────────────────────────────────
    dataset_path, dataset_label = _pick_dataset()
    if dataset_label != "cleaned":
        print(
            f"[WARNING] Cleaned dataset not found — using {dataset_label!r}.\n"
            f"          For best accuracy ensure notebooks/crop_cleaned.csv is present.\n"
            f"          Or use canonical script: python backend/train_models.py"
        )

    df = _load_dataset(dataset_path, dataset_label)

    # ── Rename raw column names to internal names ─────────────────────────────
    col_map = {"N": "nitrogen", "P": "phosphorus", "K": "potassium"}
    df = df.rename(columns=col_map)

    # ── Add humidity estimate if not present (source CSV has no humidity) ─────
    if "humidity" not in df.columns:
        df["humidity"] = np.clip(
            40.0 + 0.05 * df["rainfall"] + (30.0 - df["temperature"]),
            20.0, 100.0,
        )
        print("[prepare] Estimated humidity from temperature and rainfall.")

    # ── Ensure engineered features ────────────────────────────────────────────
    df = _ensure_engineered_features(df)

    # ── Drop rows with any remaining nulls ────────────────────────────────────
    feature_cols_crop = _BASE_FEATURES + [c for c in _ENGINEERED_FEATURES if c in df.columns]
    feature_cols_yield = feature_cols_crop + ["crop_encoded"]
    required_cols = feature_cols_crop + [_LABEL_COL, _YIELD_COL]
    before = len(df)
    df = df.dropna(subset=required_cols).reset_index(drop=True)
    if len(df) < before:
        print(f"[prepare] Dropped {before - len(df)} rows with nulls.")

    # ── Encode labels ─────────────────────────────────────────────────────────
    le = LabelEncoder()
    df["crop_encoded"] = le.fit_transform(df[_LABEL_COL].values)
    print(f"\nCrop classes ({len(le.classes_)}): {list(le.classes_)}")

    # ── Build feature matrices ────────────────────────────────────────────────
    X_crop = df[feature_cols_crop].values
    y_crop = df["crop_encoded"].values
    X_yield = df[feature_cols_yield].values
    y_yield = df[_YIELD_COL].values

    # ── Train / test split (BEFORE fitting any preprocessor) ────────────────────
    X_crop_tr_raw, X_crop_te_raw, y_crop_tr, y_crop_te = train_test_split(
        X_crop, y_crop,
        test_size=0.20, random_state=RANDOM_SEED, stratify=y_crop,
    )
    X_yield_tr_raw, X_yield_te_raw, y_yield_tr, y_yield_te = train_test_split(
        X_yield, y_yield,
        test_size=0.20, random_state=RANDOM_SEED,
    )

    # ── Scale features — fitted on training split only to prevent leakage ─────
    scaler_crop = StandardScaler()
    X_crop_tr = scaler_crop.fit_transform(X_crop_tr_raw)
    X_crop_te = scaler_crop.transform(X_crop_te_raw)

    scaler_yield = StandardScaler()
    X_yield_tr = scaler_yield.fit_transform(X_yield_tr_raw)
    X_yield_te = scaler_yield.transform(X_yield_te_raw)

    print(f"\nTrain size : {len(X_crop_tr):,}  |  Test size : {len(X_crop_te):,}")
    print(f"Crop features  ({len(feature_cols_crop)}): {feature_cols_crop}")
    print(f"Yield features ({len(feature_cols_yield)}): {feature_cols_yield}")

    # =========================================================================
    # Crop Recommendation Model
    # =========================================================================
    print("\n" + "=" * 68)
    print("  Training Crop Recommendation Model (final)")
    print("=" * 68)
    print(f"  Hyperparameters: {_RF_PARAMS}")
    print(f"  class_weight   : balanced")

    crop_model = RandomForestClassifier(
        **_RF_PARAMS,
        class_weight="balanced",
    )
    crop_model.fit(X_crop_tr, y_crop_tr)

    train_acc = accuracy_score(y_crop_tr, crop_model.predict(X_crop_tr))
    test_acc = accuracy_score(y_crop_te, crop_model.predict(X_crop_te))
    test_f1 = f1_score(y_crop_te, crop_model.predict(X_crop_te), average="weighted", zero_division=0)

    print(f"\n  Train accuracy  : {train_acc:.2%}")
    print(f"  Test  accuracy  : {test_acc:.2%}")
    print(f"  Test  F1 (wtd)  : {test_f1:.4f}")

    cv_crop = cross_val_score(
        Pipeline([("scaler", StandardScaler()), ("clf", crop_model)]),
        X_crop, y_crop,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED),
        scoring="accuracy", n_jobs=-1,
    )
    print(
        f"  5-Fold CV acc   : {cv_crop.round(4)} "
        f"→ mean={cv_crop.mean():.4f} ± {cv_crop.std():.4f}"
    )

    print("\n  Classification report (test set):")
    print(
        classification_report(
            y_crop_te,
            crop_model.predict(X_crop_te),
            target_names=le.classes_,
            zero_division=0,
        )
    )

    # =========================================================================
    # Yield Prediction Model
    # =========================================================================
    print("=" * 68)
    print("  Training Yield Prediction Model (final)")
    print("=" * 68)
    print(f"  Hyperparameters: {_RF_PARAMS}")

    yield_model = RandomForestRegressor(**_RF_PARAMS)
    yield_model.fit(X_yield_tr, y_yield_tr)

    for split_label, X_s, y_s in [
        ("Train", X_yield_tr, y_yield_tr),
        ("Test ", X_yield_te, y_yield_te),
    ]:
        y_pred = yield_model.predict(X_s)
        r2 = r2_score(y_s, y_pred)
        mae = mean_absolute_error(y_s, y_pred)
        rmse = float(np.sqrt(mean_squared_error(y_s, y_pred)))
        print(f"  {split_label}  R²={r2:.4f}  MAE={mae:.4f}  RMSE={rmse:.4f}")

    cv_yield = cross_val_score(
        Pipeline([("scaler", StandardScaler()), ("reg", yield_model)]),
        X_yield, y_yield,
        cv=5, scoring="r2", n_jobs=-1,
    )
    print(
        f"  5-Fold CV R²    : {cv_yield.round(4)} "
        f"→ mean={cv_yield.mean():.4f} ± {cv_yield.std():.4f}"
    )

    # ── Save artefacts ────────────────────────────────────────────────────────
    models_dir = os.path.join(_BACKEND_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)

    artefacts: dict[str, object] = {
        "crop_model_final.pkl": crop_model,
        "yield_model_final.pkl": yield_model,
        "label_encoder_final.pkl": le,
        "scaler_crop_final.pkl": scaler_crop,
        "scaler_yield_final.pkl": scaler_yield,
    }

    for filename, obj in artefacts.items():
        out_path = os.path.join(models_dir, filename)
        joblib.dump(obj, out_path)
        print(f"Saved: {out_path}")

    # Store feature-column metadata for the serving layer
    meta_path = os.path.join(models_dir, "feature_cols_final.pkl")
    joblib.dump(
        {"crop": feature_cols_crop, "yield": feature_cols_yield},
        meta_path,
    )
    print(f"Saved: {meta_path}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 68)
    print("  ✓ TRAINING COMPLETE — FINAL SUMMARY")
    print("=" * 68)
    print(f"  Crop accuracy (test)     : {test_acc:.2%}")
    print(f"  Crop F1 weighted (test)  : {test_f1:.4f}")
    print(f"  Crop accuracy (5-fold)   : {cv_crop.mean():.4f} ± {cv_crop.std():.4f}")
    print(f"  Yield R² (5-fold)        : {cv_yield.mean():.4f} ± {cv_yield.std():.4f}")
    print(f"  Crop classes             : {len(le.classes_)}")
    print(f"  Dataset rows used        : {len(df):,}")
    print("=" * 68)

    # Validation criteria checks
    print("\n  Validation criteria:")
    checks = [
        ("Crop accuracy > 85%",  test_acc > 0.85),
        ("Yield R² > 0.75",      cv_yield.mean() > 0.75),
        ("No class < 50 samples", all(
            (df[_LABEL_COL].value_counts() >= 50).values
        )),
        ("No null values",        df.isnull().sum().sum() == 0),
    ]
    for desc, passed in checks:
        icon = "✓" if passed else "✗"
        print(f"    {icon}  {desc}")

    print()


if __name__ == "__main__":
    train_and_save()
