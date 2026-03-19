"""
prepare_dataset.py — Load and preprocess the Crop_recommendation dataset.

Reads Crop_recommendation.csv from backend/data/, applies StandardScaler
normalization and LabelEncoder for crop labels, then saves the processed
data as NumPy arrays for use by train_model.py.

Usage:
    cd backend
    python ml_models/prepare_dataset.py
"""

from __future__ import annotations

import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

# ─── Paths ───────────────────────────────────────────────────────────────────

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACKEND_DIR = os.path.dirname(_SCRIPT_DIR)
_REPO_ROOT = os.path.dirname(_BACKEND_DIR)

DATASET_PATH = os.path.join(_REPO_ROOT, "notebooks", "Crop_Final_Updated (1).csv")
PROCESSED_DIR = os.path.join(_SCRIPT_DIR, "processed")

# ─── Feature / label columns ─────────────────────────────────────────────────

FEATURE_COLS = ["nitrogen", "phosphorus", "potassium", "temperature", "humidity", "ph", "rainfall"]
LABEL_COL = "label"


def prepare(
    dataset_path: str = DATASET_PATH,
    output_dir: str = PROCESSED_DIR,
    test_size: float = 0.20,
    random_state: int = 42,
) -> dict:
    """Load, preprocess, and save the crop recommendation dataset.

    Steps:
    1. Load CSV from *dataset_path*.
    2. Encode crop labels with LabelEncoder.
    3. Normalize features with StandardScaler.
    4. Split 80/20 into train / test sets.
    5. Save arrays + preprocessors to *output_dir*.

    Returns a dict with dataset statistics.
    """
    # ── Load ──────────────────────────────────────────────────────────────
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(
            f"Dataset not found at {dataset_path!r}. "
            "Ensure 'Crop_Final_Updated (1).csv' is present in the notebooks/ directory."
        )

    df = pd.read_csv(dataset_path)
    print(f"Dataset loaded: {dataset_path}")
    print(f"  Shape        : {df.shape}")
    print(f"  Columns      : {list(df.columns)}")
    print(f"  Crop classes : {df[LABEL_COL].nunique()} ({sorted(df[LABEL_COL].unique().tolist())})")
    missing = df.isnull().sum()
    if missing.any():
        print(f"  Missing values:\n{missing[missing > 0]}")
    else:
        print("  Missing values : none")

    # ── Rename source columns to expected names ───────────────────────────
    df = df.rename(columns={"N": "nitrogen", "P": "phosphorus", "K": "potassium"})

    # ── Estimate humidity if not in source CSV ────────────────────────────
    if "humidity" not in df.columns:
        df["humidity"] = np.clip(
            40.0 + 0.05 * df["rainfall"] + (30.0 - df["temperature"]),
            20.0, 100.0,
        )
        print("  humidity      : estimated from temperature and rainfall")

    # ── Encode labels ─────────────────────────────────────────────────────
    le = LabelEncoder()
    y = le.fit_transform(df[LABEL_COL])
    X = df[FEATURE_COLS].values

    print(f"\nLabel encoder: {len(le.classes_)} classes → {list(le.classes_)}")

    # ── Train / test split ────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    print(f"\nTrain samples: {len(X_train)}")
    print(f"Test  samples: {len(X_test)}")

    # ── Normalize features ────────────────────────────────────────────────
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print(f"\nStandardScaler fitted on train set.")
    print(f"  Feature means : {scaler.mean_.round(4)}")
    print(f"  Feature stds  : {scaler.scale_.round(4)}")

    # ── Save ─────────────────────────────────────────────────────────────
    os.makedirs(output_dir, exist_ok=True)

    np.save(os.path.join(output_dir, "X_train.npy"), X_train_scaled)
    np.save(os.path.join(output_dir, "X_test.npy"), X_test_scaled)
    np.save(os.path.join(output_dir, "y_train.npy"), y_train)
    np.save(os.path.join(output_dir, "y_test.npy"), y_test)

    joblib.dump(scaler, os.path.join(output_dir, "scaler.pkl"))
    joblib.dump(le, os.path.join(output_dir, "label_encoder.pkl"))

    print(f"\nSaved processed data to {output_dir}/")

    stats = {
        "n_samples": len(df),
        "n_features": len(FEATURE_COLS),
        "n_classes": len(le.classes_),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "crop_classes": list(le.classes_),
        "feature_names": FEATURE_COLS,
    }
    return stats


if __name__ == "__main__":
    stats = prepare()
    print(f"\nDataset preparation complete.")
    print(f"  Total samples : {stats['n_samples']}")
    print(f"  Features      : {stats['n_features']}")
    print(f"  Crop classes  : {stats['n_classes']}")
