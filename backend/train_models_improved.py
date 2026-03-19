"""
train_models_improved.py — Train improved crop and yield models.

Improvements over train_models.py
----------------------------------
* Uses the cleaned dataset (Crop_recommendation_improved.csv) which has
  underrepresented crops and extreme yield outliers removed.
* Adds five engineered features (NPK_total, NPK_ratio, Climate_score,
  Temp_humidity_interaction, Soil_quality_score).
* Applies StandardScaler normalisation to all numeric inputs.
* Uses class_weight='balanced' for the crop classifier to handle any
  residual class imbalance.
* Better Random Forest hyper-parameters (max_depth=15, min_samples_leaf=5).
* 5-fold stratified cross-validation.

Trained artefacts are saved to backend/models/ alongside the originals
so the FastAPI service can load them via config.

Usage:
    cd backend
    python train_models_improved.py

    # Or from the repository root:
    python backend/train_models_improved.py
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
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_BACKEND_DIR)

# Prefer the improved (cleaned + engineered) dataset; fall back to the
# single authoritative source dataset when the generated file is absent.
_IMPROVED_DATASET = os.path.join(_REPO_ROOT, "notebooks", "Crop_recommendation_improved.csv")
_FALLBACK_DATASET = os.path.join(_REPO_ROOT, "notebooks", "Crop_Final_Updated (1).csv")

# Add scripts/ to path so feature_engineering is importable
_SCRIPTS_DIR = os.path.join(_REPO_ROOT, "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

# ---------------------------------------------------------------------------
# Feature columns
# ---------------------------------------------------------------------------
_BASE_FEATURES = ["nitrogen", "phosphorus", "potassium", "temperature", "humidity", "ph", "rainfall"]
_ENGINEERED_FEATURES = [
    "NPK_total",
    "NPK_ratio",
    "Climate_score",
    "Temp_humidity_interaction",
    "Soil_quality_score",
]
_LABEL_COL = "label"
_YIELD_COL = "yield"


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def _load_dataset(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found at {path!r}. "
            "Run scripts/clean_and_improve_dataset.py first to generate it."
        )
    df = pd.read_csv(path)
    print(f"[load] {path}")
    print(f"       shape={df.shape}  crops={df[_LABEL_COL].nunique()}")
    null_count = df.isnull().sum().sum()
    if null_count:
        print(f"       ⚠ {null_count} null values found — will be dropped.")
    else:
        print("       ✓ No null values.")
    return df


def _ensure_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add engineered features if they are not already present."""
    missing_eng = [c for c in _ENGINEERED_FEATURES if c not in df.columns]
    if missing_eng:
        print(f"[features] Engineered columns not found — computing them now…")
        try:
            from feature_engineering import add_features
            df = add_features(df)
            print(f"[features] Added: {_ENGINEERED_FEATURES}")
        except ImportError:
            print("[features] WARNING: feature_engineering module not found. "
                  "Engineered features will be skipped.")
    return df


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_and_save() -> None:
    # ── Load dataset ────────────────────────────────────────────────────────
    dataset_path = _IMPROVED_DATASET if os.path.exists(_IMPROVED_DATASET) else _FALLBACK_DATASET
    if dataset_path == _FALLBACK_DATASET:
        print("[WARNING] Improved dataset not found — using source dataset.")
        print(f"          Run:  python scripts/clean_and_improve_dataset.py")
        print(f"          Or train directly:  python backend/train_models.py")

    df = _load_dataset(dataset_path)

    # ── Rename raw column names to internal names ────────────────────────────
    col_map = {"N": "nitrogen", "P": "phosphorus", "K": "potassium"}
    df = df.rename(columns=col_map)

    # ── Add humidity estimate if not present (source CSV has no humidity) ────
    if "humidity" not in df.columns:
        df["humidity"] = np.clip(
            40.0 + 0.05 * df["rainfall"] + (30.0 - df["temperature"]),
            20.0, 100.0,
        )
        print("[prepare] Estimated humidity from temperature and rainfall.")

    # ── Ensure engineered features ───────────────────────────────────────────
    df = _ensure_engineered_features(df)

    # ── Drop rows with any nulls ─────────────────────────────────────────────
    all_feature_cols = _BASE_FEATURES + [c for c in _ENGINEERED_FEATURES if c in df.columns]
    required_cols = all_feature_cols + [_LABEL_COL, _YIELD_COL]
    present_required = [c for c in required_cols if c in df.columns]
    before = len(df)
    df = df.dropna(subset=present_required).reset_index(drop=True)
    if len(df) < before:
        print(f"[prepare] Dropped {before - len(df)} rows with nulls.")

    # ── Encode labels ────────────────────────────────────────────────────────
    le = LabelEncoder()
    df["crop_encoded"] = le.fit_transform(df[_LABEL_COL].values)

    print(f"\nCrop classes ({len(le.classes_)}): {list(le.classes_)}")

    # ── Build feature matrices ───────────────────────────────────────────────
    feature_cols_crop = _BASE_FEATURES + [c for c in _ENGINEERED_FEATURES if c in df.columns]
    feature_cols_yield = feature_cols_crop + ["crop_encoded"]

    X_crop = df[feature_cols_crop].values
    y_crop = df["crop_encoded"].values
    X_yield = df[feature_cols_yield].values
    y_yield = df[_YIELD_COL].values

    # ── Train / test split (BEFORE fitting any preprocessor) ────────────────
    X_crop_tr_raw, X_crop_te_raw, y_crop_tr, y_crop_te = train_test_split(
        X_crop, y_crop, test_size=0.20, random_state=RANDOM_SEED, stratify=y_crop
    )
    X_yield_tr_raw, X_yield_te_raw, y_yield_tr, y_yield_te = train_test_split(
        X_yield, y_yield, test_size=0.20, random_state=RANDOM_SEED
    )

    # ── Scale features — fitted on training split only to prevent leakage ────
    scaler_crop = StandardScaler()
    X_crop_tr = scaler_crop.fit_transform(X_crop_tr_raw)
    X_crop_te = scaler_crop.transform(X_crop_te_raw)

    scaler_yield = StandardScaler()
    X_yield_tr = scaler_yield.fit_transform(X_yield_tr_raw)
    X_yield_te = scaler_yield.transform(X_yield_te_raw)

    print(f"\nTrain size: {len(X_crop_tr)} | Test size: {len(X_crop_te)}")
    print(f"Features used for crop model  : {len(feature_cols_crop)} — {feature_cols_crop}")
    print(f"Features used for yield model : {len(feature_cols_yield)}")

    # ── Crop Recommendation Model ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Training Crop Recommendation Model (improved)")
    print("=" * 60)

    crop_model = RandomForestClassifier(
        n_estimators=300,
        max_depth=15,
        min_samples_leaf=5,
        max_features="sqrt",
        class_weight="balanced",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    crop_model.fit(X_crop_tr, y_crop_tr)

    train_acc = accuracy_score(y_crop_tr, crop_model.predict(X_crop_tr))
    test_acc = accuracy_score(y_crop_te, crop_model.predict(X_crop_te))
    print(f"  Train accuracy : {train_acc:.2%}")
    print(f"  Test  accuracy : {test_acc:.2%}")

    cv_crop = cross_val_score(
        Pipeline([("scaler", StandardScaler()), ("clf", crop_model)]),
        X_crop, y_crop, cv=5, scoring="accuracy", n_jobs=-1
    )
    print(f"  5-Fold CV acc  : {cv_crop.round(4)} → mean={cv_crop.mean():.4f} ± {cv_crop.std():.4f}")

    print("\n  Classification report (test set):")
    print(
        classification_report(
            y_crop_te,
            crop_model.predict(X_crop_te),
            target_names=le.classes_,
            zero_division=0,
        )
    )

    # ── Yield Prediction Model ────────────────────────────────────────────────
    print("=" * 60)
    print("Training Yield Prediction Model (improved)")
    print("=" * 60)

    yield_model = RandomForestRegressor(
        n_estimators=300,
        max_depth=15,
        min_samples_leaf=5,
        max_features="sqrt",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    yield_model.fit(X_yield_tr, y_yield_tr)

    for label, X_s, y_s in [("Train", X_yield_tr, y_yield_tr), ("Test ", X_yield_te, y_yield_te)]:
        y_pred = yield_model.predict(X_s)
        r2 = r2_score(y_s, y_pred)
        mae = mean_absolute_error(y_s, y_pred)
        rmse = float(np.sqrt(mean_squared_error(y_s, y_pred)))
        print(f"  {label}  R²={r2:.4f}  MAE={mae:.4f}  RMSE={rmse:.4f}")

    cv_yield = cross_val_score(
        Pipeline([("scaler", StandardScaler()), ("reg", yield_model)]),
        X_yield, y_yield, cv=5, scoring="r2", n_jobs=-1
    )
    print(f"  5-Fold CV R²   : {cv_yield.round(4)} → mean={cv_yield.mean():.4f} ± {cv_yield.std():.4f}")

    # ── Save artefacts ────────────────────────────────────────────────────────
    models_dir = os.path.join(_BACKEND_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)

    artefacts = {
        "crop_model_improved.pkl": crop_model,
        "yield_model_improved.pkl": yield_model,
        "label_encoder_improved.pkl": le,
        "scaler_crop_improved.pkl": scaler_crop,
        "scaler_yield_improved.pkl": scaler_yield,
    }

    for filename, obj in artefacts.items():
        path = os.path.join(models_dir, filename)
        joblib.dump(obj, path)
        print(f"Saved: {path}")

    # Also store the list of feature columns used so the service can
    # reconstruct the input vector in the correct order.
    meta_path = os.path.join(models_dir, "feature_cols_improved.pkl")
    joblib.dump(
        {"crop": feature_cols_crop, "yield": feature_cols_yield},
        meta_path,
    )
    print(f"Saved: {meta_path}")

    print(f"\n✓ Crop accuracy (test)  : {test_acc:.2%}")
    cv_yield_mean = cv_yield.mean()
    print(f"✓ Yield R² (5-fold CV)  : {cv_yield_mean:.4f}")
    print(f"✓ Crop classes          : {len(le.classes_)}")
    print(f"✓ Dataset rows used     : {len(df):,}")


if __name__ == "__main__":
    train_and_save()
