"""
train_models.py — Generate crop recommendation and yield prediction models.

Creates two Random Forest models with synthetic training data based on
realistic crop-growing conditions:
  1. crop_model.pkl  — Random Forest Classifier (predicts crop label)
  2. yield_model.pkl — Random Forest Regressor  (predicts yield in tons/hectare)

Usage:
    cd backend
    python train_models.py
"""

from __future__ import annotations

import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib

# ─── Synthetic training data ─────────────────────────────────────────────────
# Each entry: (crop, N_range, P_range, K_range, temp_range, humidity_range, ph_range, rainfall_range, yield_range)

CROP_PROFILES = [
    ("Rice",       (60, 100), (30, 60),  (30, 50),  (20, 35), (70, 95), (5.5, 7.0), (150, 300), (3.0, 5.5)),
    ("Wheat",      (40, 80),  (30, 60),  (20, 40),  (12, 25), (50, 75), (6.0, 7.5), (50, 150),  (2.5, 4.5)),
    ("Maize",      (60, 120), (35, 70),  (20, 50),  (18, 32), (55, 80), (5.5, 7.5), (60, 200),  (3.5, 6.0)),
    ("Soybean",    (20, 60),  (40, 80),  (20, 50),  (20, 30), (60, 85), (6.0, 7.0), (60, 180),  (1.5, 3.5)),
    ("Cotton",     (60, 120), (20, 50),  (20, 50),  (22, 35), (50, 75), (6.0, 8.0), (50, 150),  (1.5, 3.0)),
    ("Sugarcane",  (80, 140), (40, 80),  (30, 60),  (22, 36), (70, 90), (5.5, 7.5), (100, 250), (50, 80)),
    ("Potato",     (40, 80),  (50, 90),  (60, 120), (12, 22), (60, 80), (5.0, 6.5), (50, 150),  (15, 30)),
    ("Tomato",     (50, 100), (40, 80),  (40, 80),  (18, 30), (60, 85), (5.5, 7.0), (50, 150),  (20, 40)),
    ("Banana",     (80, 120), (30, 60),  (40, 80),  (24, 35), (70, 95), (5.5, 7.0), (100, 250), (15, 35)),
    ("Mango",      (40, 80),  (20, 50),  (30, 60),  (24, 38), (50, 80), (5.5, 7.5), (50, 200),  (5, 15)),
    ("Groundnut",  (20, 40),  (30, 60),  (20, 40),  (22, 32), (55, 80), (6.0, 7.0), (40, 120),  (1.0, 2.5)),
    ("Jute",       (60, 100), (20, 50),  (30, 60),  (24, 36), (75, 95), (6.0, 7.5), (150, 300), (2.0, 3.5)),
]

SAMPLES_PER_CROP = 200
RANDOM_SEED = 42


def _generate_data() -> pd.DataFrame:
    """Generate synthetic training data for all crops."""
    rng = np.random.default_rng(RANDOM_SEED)
    rows: list[dict] = []

    for crop, n_r, p_r, k_r, t_r, h_r, ph_r, rain_r, y_r in CROP_PROFILES:
        for _ in range(SAMPLES_PER_CROP):
            n = rng.uniform(*n_r)
            p = rng.uniform(*p_r)
            k = rng.uniform(*k_r)
            temp = rng.uniform(*t_r)
            hum = rng.uniform(*h_r)
            ph = rng.uniform(*ph_r)
            rain = rng.uniform(*rain_r)

            # Yield correlates with feature quality + some noise
            base_yield = rng.uniform(*y_r)
            noise = rng.normal(0, (y_r[1] - y_r[0]) * 0.05)
            crop_yield = max(y_r[0] * 0.5, base_yield + noise)

            rows.append({
                "nitrogen": round(n, 1),
                "phosphorus": round(p, 1),
                "potassium": round(k, 1),
                "temperature": round(temp, 1),
                "humidity": round(hum, 1),
                "ph": round(ph, 2),
                "rainfall": round(rain, 1),
                "crop": crop,
                "yield": round(crop_yield, 2),
            })

    return pd.DataFrame(rows)


def train_and_save() -> None:
    """Train both models and save them as .pkl files."""
    df = _generate_data()

    # Encode crop labels
    le = LabelEncoder()
    df["crop_encoded"] = le.fit_transform(df["crop"])

    features_crop = ["nitrogen", "phosphorus", "potassium", "temperature", "humidity", "ph", "rainfall"]
    features_yield = features_crop + ["crop_encoded"]

    X_crop = df[features_crop].values
    y_crop = df["crop_encoded"].values

    X_yield = df[features_yield].values
    y_yield = df["yield"].values

    # ── Crop Recommendation Model ────────────────────────────────────────
    crop_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    crop_model.fit(X_crop, y_crop)
    accuracy = crop_model.score(X_crop, y_crop)
    print(f"Crop model training accuracy: {accuracy:.2%}")

    # ── Yield Prediction Model ───────────────────────────────────────────
    yield_model = RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    yield_model.fit(X_yield, y_yield)
    r2 = yield_model.score(X_yield, y_yield)
    print(f"Yield model training R²: {r2:.4f}")

    # ── Save artifacts ───────────────────────────────────────────────────
    models_dir = os.path.join(os.path.dirname(__file__), "models")
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
    print(f"\nCrop classes: {list(le.classes_)}")


if __name__ == "__main__":
    train_and_save()
