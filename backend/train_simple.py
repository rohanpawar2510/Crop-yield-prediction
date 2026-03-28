"""
train_simple.py — Simple 8-feature training script for crop yield prediction.

Uses ONLY the raw dataset features (no feature engineering):
  - nitrogen (N)
  - phosphorus (P)
  - potassium (K)
  - temperature
  - humidity
  - ph
  - rainfall
  - crop_encoded (derived from the label column)

Artefacts saved to backend/models/:
  crop_model_simple.pkl       — Pipeline(StandardScaler + RandomForestClassifier)
  yield_model_simple.pkl      — RandomForestRegressor (8 features)
  label_encoder_simple.pkl    — LabelEncoder for crop names
  scaler_yield_simple.pkl     — StandardScaler fitted on yield training split only

Usage:
    cd backend
    python train_simple.py
"""

from __future__ import annotations

import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

RANDOM_SEED = 42

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# Prefer the embedded CSV; fall back to the notebooks directory
_DATASET_CANDIDATES = [
    os.path.join(_BACKEND_DIR, "data", "Crop_recommendation.csv"),
]

_BASE_FEATURES = [
    "nitrogen", "phosphorus", "potassium",
    "temperature", "humidity", "ph", "rainfall",
]


def _find_dataset() -> str:
    for path in _DATASET_CANDIDATES:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        "Dataset not found. Expected one of:\n"
        + "\n".join(f"  {p}" for p in _DATASET_CANDIDATES)
    )


def train_and_save() -> None:
    """Load dataset, train simple models, and save artefacts."""

    # ── Load ─────────────────────────────────────────────────────────────────
    dataset_path = _find_dataset()
    df = pd.read_csv(dataset_path)
    print(f"[load] {dataset_path}")
    print(f"       shape={df.shape}")

    # ── Rename source column names to internal names ──────────────────────────
    df = df.rename(columns={"N": "nitrogen", "P": "phosphorus", "K": "potassium"})

    # ── Encode crop labels ────────────────────────────────────────────────────
    le = LabelEncoder()
    df["crop_encoded"] = le.fit_transform(df["label"].str.lower().values)
    print(f"Crop classes ({len(le.classes_)}): {list(le.classes_)}")

    # ── Build feature matrices ────────────────────────────────────────────────
    yield_features = _BASE_FEATURES + ["crop_encoded"]

    X_crop = df[_BASE_FEATURES].values
    y_crop = df["crop_encoded"].values
    X_yield = df[yield_features].values
    y_yield = df["yield"].values

    # ── Train / test split ────────────────────────────────────────────────────
    X_crop_train, X_crop_test, y_crop_train, y_crop_test = train_test_split(
        X_crop, y_crop,
        test_size=0.20, random_state=RANDOM_SEED, stratify=y_crop,
    )
    X_yield_train, X_yield_test, y_yield_train, y_yield_test = train_test_split(
        X_yield, y_yield,
        test_size=0.20, random_state=RANDOM_SEED,
    )
    print(f"\nTrain size: {len(X_crop_train):,} | Test size: {len(X_crop_test):,}")

    # =========================================================================
    # Crop Classification Model
    # =========================================================================
    print("\n" + "=" * 60)
    print("  Training Crop Classification Model")
    print("=" * 60)

    crop_model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=200,
            max_depth=None,
            min_samples_leaf=1,
            max_features="sqrt",
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )),
    ])
    crop_model.fit(X_crop_train, y_crop_train)

    train_acc = accuracy_score(y_crop_train, crop_model.predict(X_crop_train))
    test_acc = accuracy_score(y_crop_test, crop_model.predict(X_crop_test))
    print(f"  Train accuracy : {train_acc:.2%}")
    print(f"  Test  accuracy : {test_acc:.2%}")

    # =========================================================================
    # Yield Prediction Model (8 features: 7 base + crop_encoded)
    # =========================================================================
    print("\n" + "=" * 60)
    print("  Training Yield Prediction Model (8 features)")
    print("=" * 60)

    scaler_yield = StandardScaler()
    X_yield_train_sc = scaler_yield.fit_transform(X_yield_train)
    X_yield_test_sc = scaler_yield.transform(X_yield_test)

    yield_model = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        min_samples_leaf=2,
        max_features="sqrt",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    yield_model.fit(X_yield_train_sc, y_yield_train)

    for split_lbl, X_s, y_s in [
        ("Train", X_yield_train_sc, y_yield_train),
        ("Test ", X_yield_test_sc, y_yield_test),
    ]:
        y_pred = yield_model.predict(X_s)
        r2 = r2_score(y_s, y_pred)
        mae = mean_absolute_error(y_s, y_pred)
        rmse = float(np.sqrt(mean_squared_error(y_s, y_pred)))
        print(f"  {split_lbl}  R²={r2:.4f}  MAE={mae:.4f}  RMSE={rmse:.4f}")

    print(f"\n  Yield model feature count: {yield_model.n_features_in_}")

    # ── Save artefacts ────────────────────────────────────────────────────────
    models_dir = os.path.join(_BACKEND_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)

    artefacts: dict = {
        "crop_model_simple.pkl":    crop_model,
        "yield_model_simple.pkl":   yield_model,
        "label_encoder_simple.pkl": le,
        "scaler_yield_simple.pkl":  scaler_yield,
    }

    for filename, obj in artefacts.items():
        out_path = os.path.join(models_dir, filename)
        joblib.dump(obj, out_path)
        print(f"Saved: {out_path}")

    print("\n" + "=" * 60)
    print("  ✓ TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Dataset      : {dataset_path}")
    print(f"  Rows         : {len(df):,}")
    print(f"  Crop classes : {len(le.classes_)}")
    print(f"  Crop test acc: {test_acc:.2%}")
    print(f"  Yield features: {yield_features}")
    print("=" * 60)


if __name__ == "__main__":
    train_and_save()
