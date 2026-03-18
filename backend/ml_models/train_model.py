"""
train_model.py — Train a RandomForestClassifier on the prepared crop dataset.

Loads preprocessed data from ml_models/processed/ (produced by
prepare_dataset.py), trains a RandomForestClassifier with 200 trees, and
saves the trained model, metadata, and feature importances.

Expected test accuracy: ≥ 98%

Usage:
    cd backend
    python ml_models/prepare_dataset.py   # first time only
    python ml_models/train_model.py
"""

from __future__ import annotations

import json
import os

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# ─── Paths ───────────────────────────────────────────────────────────────────

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PROCESSED_DIR = os.path.join(_SCRIPT_DIR, "processed")
MODELS_DIR = os.path.join(_SCRIPT_DIR, "models")

# ─── Model hyper-parameters ──────────────────────────────────────────────────

N_ESTIMATORS = 200
MAX_DEPTH = None
MIN_SAMPLES_SPLIT = 2
RANDOM_STATE = 42

FEATURE_NAMES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]


def train(processed_dir: str = PROCESSED_DIR, models_dir: str = MODELS_DIR) -> dict:
    """Load prepared data, train a RandomForestClassifier and save artifacts.

    Returns a dict with training results including accuracy metrics.
    """
    # ── Load processed data ───────────────────────────────────────────────
    for fname in ("X_train.npy", "X_test.npy", "y_train.npy", "y_test.npy",
                  "scaler.pkl", "label_encoder.pkl"):
        if not os.path.exists(os.path.join(processed_dir, fname)):
            raise FileNotFoundError(
                f"Processed file '{fname}' not found in {processed_dir!r}. "
                "Run prepare_dataset.py first."
            )

    X_train = np.load(os.path.join(processed_dir, "X_train.npy"))
    X_test = np.load(os.path.join(processed_dir, "X_test.npy"))
    y_train = np.load(os.path.join(processed_dir, "y_train.npy"))
    y_test = np.load(os.path.join(processed_dir, "y_test.npy"))
    le = joblib.load(os.path.join(processed_dir, "label_encoder.pkl"))

    print(f"Loaded train: {X_train.shape}, test: {X_test.shape}")
    print(f"Crop classes ({len(le.classes_)}): {list(le.classes_)}")

    # ── Train ─────────────────────────────────────────────────────────────
    print(f"\n=== Training RandomForestClassifier ===")
    print(f"  n_estimators     : {N_ESTIMATORS}")
    print(f"  max_depth        : {MAX_DEPTH}")
    print(f"  min_samples_split: {MIN_SAMPLES_SPLIT}")
    print(f"  random_state     : {RANDOM_STATE}")

    model = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        min_samples_split=MIN_SAMPLES_SPLIT,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # ── Evaluate ──────────────────────────────────────────────────────────
    train_acc = accuracy_score(y_train, model.predict(X_train))
    test_acc = accuracy_score(y_test, model.predict(X_test))

    print(f"\n  Training Accuracy : {train_acc:.2%}")
    print(f"  Testing  Accuracy : {test_acc:.2%}")

    print("\n  Classification Report (test set):")
    print(
        classification_report(
            y_test,
            model.predict(X_test),
            target_names=le.classes_,
            zero_division=0,
        )
    )

    # ── Feature importance ────────────────────────────────────────────────
    importances = model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    print("  Feature Importances:")
    for i in sorted_idx:
        print(f"    {FEATURE_NAMES[i]:<15}: {importances[i]:.4f} ({importances[i]*100:.1f}%)")

    # ── Save artifacts ────────────────────────────────────────────────────
    os.makedirs(models_dir, exist_ok=True)

    model_path = os.path.join(models_dir, "crop_classifier.pkl")
    joblib.dump(model, model_path)
    print(f"\nSaved model → {model_path}")

    metadata = {
        "algorithm": "RandomForestClassifier",
        "n_estimators": N_ESTIMATORS,
        "max_depth": MAX_DEPTH,
        "min_samples_split": MIN_SAMPLES_SPLIT,
        "random_state": RANDOM_STATE,
        "train_accuracy": round(train_acc * 100, 2),
        "test_accuracy": round(test_acc * 100, 2),
        "n_classes": int(len(le.classes_)),
        "crop_classes": list(le.classes_),
        "feature_names": FEATURE_NAMES,
        "feature_importances": {
            FEATURE_NAMES[i]: round(float(importances[i]), 6)
            for i in range(len(FEATURE_NAMES))
        },
    }

    meta_path = os.path.join(models_dir, "metadata.json")
    with open(meta_path, "w") as fh:
        json.dump(metadata, fh, indent=2)
    print(f"Saved metadata → {meta_path}")

    return metadata


if __name__ == "__main__":
    meta = train()
    print(f"\nTraining complete.")
    print(f"  Train accuracy : {meta['train_accuracy']}%")
    print(f"  Test  accuracy : {meta['test_accuracy']}%")
