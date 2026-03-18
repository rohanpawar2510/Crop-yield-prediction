"""
train_models.py — Train crop recommendation and yield prediction models.

Loads the real crop dataset (``Crop_recommendation.csv``) from the
``notebooks/`` directory and trains two Random Forest models:
  1. crop_model.pkl  — Random Forest Classifier (predicts crop label)
  2. yield_model.pkl — Random Forest Regressor  (predicts yield in tons/hectare)

Dataset columns expected:
  N, P, K, temperature, humidity, ph, rainfall, label, yield

Usage:
    cd backend
    python train_models.py
"""

from __future__ import annotations

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
import joblib

RANDOM_SEED = 42

# ─── Dataset location ────────────────────────────────────────────────────────
# Path relative to this file: ../notebooks/Crop_recommendation.csv
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_DATASET_PATH = os.path.join(_BACKEND_DIR, "..", "notebooks", "Crop_recommendation.csv")

# Column names in the dataset
_FEATURE_COLS = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
_LABEL_COL = "label"
_YIELD_COL = "yield"

# Internal feature names used by the prediction service
_INTERNAL_FEATURE_NAMES = ["nitrogen", "phosphorus", "potassium", "temperature", "humidity", "ph", "rainfall"]


def _load_dataset(path: str) -> pd.DataFrame:
    """Load the crop recommendation dataset from a CSV file."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found at {path!r}. "
            "Ensure 'Crop_recommendation.csv' is present in the notebooks/ directory."
        )
    df = pd.read_csv(path)
    print(f"Dataset loaded: {path}")
    print(f"  Shape       : {df.shape}")
    print(f"  Columns     : {list(df.columns)}")
    print(f"  Crops ({df[_LABEL_COL].nunique()}): {sorted(df[_LABEL_COL].unique().tolist())}")
    missing = df.isnull().sum()
    if missing.any():
        print(f"  Missing values:\n{missing[missing > 0]}")
    else:
        print("  Missing values: none")
    return df


def train_and_save() -> None:
    """Load the real dataset, train both models and save them as .pkl files."""
    df = _load_dataset(_DATASET_PATH)

    # ── Rename dataset columns to internal names used by the service ────
    col_map = {
        "N": "nitrogen",
        "P": "phosphorus",
        "K": "potassium",
        _LABEL_COL: "crop",
    }
    df = df.rename(columns=col_map)

    # Drop rows with missing values in required columns
    required = _INTERNAL_FEATURE_NAMES + ["crop", _YIELD_COL]
    before = len(df)
    df = df.dropna(subset=required).reset_index(drop=True)
    if len(df) < before:
        print(f"  Dropped {before - len(df)} rows with missing values.")

    # Encode crop labels
    le = LabelEncoder()
    df["crop_encoded"] = le.fit_transform(df["crop"])

    features_crop = _INTERNAL_FEATURE_NAMES
    features_yield = features_crop + ["crop_encoded"]

    X_crop = df[features_crop].values
    y_crop = df["crop_encoded"].values

    X_yield = df[features_yield].values
    y_yield = df[_YIELD_COL].values

    # ── Train / test split ───────────────────────────────────────────────
    X_crop_train, X_crop_test, y_crop_train, y_crop_test = train_test_split(
        X_crop, y_crop, test_size=0.20, random_state=RANDOM_SEED, stratify=y_crop
    )
    X_yield_train, X_yield_test, y_yield_train, y_yield_test = train_test_split(
        X_yield, y_yield, test_size=0.20, random_state=RANDOM_SEED
    )

    print(f"\nTrain size: {len(X_crop_train)} | Test size: {len(X_crop_test)}")

    # ── Crop Recommendation Model ────────────────────────────────────────
    print("\n=== Training Crop Recommendation Model ===")
    crop_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_leaf=1,
        max_features="sqrt",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    crop_model.fit(X_crop_train, y_crop_train)

    train_acc = accuracy_score(y_crop_train, crop_model.predict(X_crop_train))
    test_acc = accuracy_score(y_crop_test, crop_model.predict(X_crop_test))
    print(f"  Train accuracy : {train_acc:.2%}")
    print(f"  Test  accuracy : {test_acc:.2%}")

    cv_crop = cross_val_score(crop_model, X_crop_train, y_crop_train, cv=5, scoring="accuracy", n_jobs=-1)
    print(f"  5-Fold CV acc  : {cv_crop.round(4)} → mean={cv_crop.mean():.4f} ± {cv_crop.std():.4f}")

    print("\n  Classification report (test set):")
    print(
        classification_report(
            y_crop_test,
            crop_model.predict(X_crop_test),
            target_names=le.classes_,
            zero_division=0,
        )
    )

    # ── Yield Prediction Model ───────────────────────────────────────────
    print("=== Training Yield Prediction Model ===")
    yield_model = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        min_samples_leaf=2,
        max_features="sqrt",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    yield_model.fit(X_yield_train, y_yield_train)

    for label, X_s, y_s in [("Train", X_yield_train, y_yield_train), ("Test ", X_yield_test, y_yield_test)]:
        y_pred = yield_model.predict(X_s)
        r2   = r2_score(y_s, y_pred)
        mae  = mean_absolute_error(y_s, y_pred)
        rmse = float(np.sqrt(mean_squared_error(y_s, y_pred)))
        print(f"  {label}  R²={r2:.4f}  MAE={mae:.4f}  RMSE={rmse:.4f}")

    cv_yield = cross_val_score(yield_model, X_yield_train, y_yield_train, cv=5, scoring="r2", n_jobs=-1)
    print(f"  5-Fold CV R²   : {cv_yield.round(4)} → mean={cv_yield.mean():.4f} ± {cv_yield.std():.4f}")

    # ── Save artifacts ───────────────────────────────────────────────────
    models_dir = os.path.join(_BACKEND_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)

    crop_path = os.path.join(models_dir, "crop_model.pkl")
    yield_path = os.path.join(models_dir, "yield_model.pkl")
    encoder_path = os.path.join(models_dir, "label_encoder.pkl")

    joblib.dump(crop_model, crop_path)
    joblib.dump(yield_model, yield_path)
    joblib.dump(le, encoder_path)

    print(f"\nSaved: {crop_path}")
    print(f"Saved: {yield_path}")
    print(f"Saved: {encoder_path}")
    print(f"\nCrop classes ({len(le.classes_)}): {list(le.classes_)}")


if __name__ == "__main__":
    train_and_save()
