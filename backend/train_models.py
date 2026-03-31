"""
train_models.py — Canonical training script for crop recommendation.

Single authoritative source dataset: notebooks/Final_Agriculture_Dataset_ML_Final.csv

Dataset schema:
  Columns: N, P, K, temperature, ph, rainfall, label, yield,
           district_name, Season, Area
  Note: yield is already log-transformed in the dataset.

Data cleaning pipeline (inline):
  1. Rename columns (N→nitrogen, P→phosphorus, K→potassium,
     Area→area, district_name→district, Season→season).
  2. Remove crops with fewer than MIN_SAMPLES_PER_CROP samples.
  3. Remove yield outliers beyond OUTLIER_SIGMA standard deviations per crop.
  4. Cap at MAX_SAMPLES_PER_CROP rows per crop (class balance).
  5. Add four engineered features.

Training:
  - Split train/test FIRST (20 % held-out, stratified).
  - StandardScaler embedded in a Pipeline so CV / inference are always leak-free.
  - RandomForestClassifier (n_estimators=300, class_weight=balanced).
  - Reports train accuracy, test accuracy, 5-fold CV score, and classification
    report.

Artefacts saved to backend/models/:
  crop_model.pkl       — sklearn Pipeline (StandardScaler + RandomForest)
  yield_model.pkl      — RandomForestRegressor
  label_encoder.pkl    — LabelEncoder for crop names
  scaler_yield.pkl     — StandardScaler fitted on yield training split only
  feature_cols.pkl     — {'crop': [...], 'yield': [...]} feature column lists

Expected accuracy: ≥ 90 % crop classification on the test set.

Usage:
    cd backend
    python train_models.py
"""

from __future__ import annotations

import json
import os

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
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

RANDOM_SEED = 42
MIN_SAMPLES_PER_CROP = 100   # crops below this threshold are dropped
MAX_SAMPLES_PER_CROP = 1000  # hard cap per crop for class balance
OUTLIER_SIGMA = 2.5          # yield outlier threshold in standard deviations

# ─── Dataset location ────────────────────────────────────────────────────────
# Single authoritative source; script fails with a clear error if missing.
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_BACKEND_DIR)
_DATASET_PATH = os.path.join(_REPO_ROOT, "notebooks", "Final_Agriculture_Dataset_ML_Final.csv")

_LABEL_COL = "label"
_YIELD_COL = "yield"

_BASE_FEATURES = [
    "nitrogen", "phosphorus", "potassium",
    "temperature", "ph", "rainfall",
    "district", "season", "area",
]
_ENGINEERED_FEATURES = [
    "NPK_total",
    "NPK_ratio",
    "Climate_score",
    "Soil_quality_score",
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with four additional engineered columns."""
    df = df.copy()
    df["NPK_total"] = df["nitrogen"] + df["phosphorus"] + df["potassium"]
    df["NPK_ratio"] = df["nitrogen"] / (df["phosphorus"] + df["potassium"] + 1e-6)
    df["Climate_score"] = (
        0.5 * df["temperature"]       # equal weights: temperature
        + 0.5 * (df["rainfall"] / 100.0)  # and normalised rainfall (per 100 mm)
    )
    df["Soil_quality_score"] = 10.0 * np.exp(-0.5 * ((df["ph"] - 6.5) / 0.8) ** 2)
    return df


def _clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Apply cleaning pipeline: filter rare crops, remove outliers, balance."""
    # Step 1: Remove crops with insufficient samples
    counts = df[_LABEL_COL].value_counts()
    valid_crops = counts[counts >= MIN_SAMPLES_PER_CROP].index
    removed_crops = sorted(set(counts.index) - set(valid_crops))
    n_before = len(df)
    df = df[df[_LABEL_COL].isin(valid_crops)].reset_index(drop=True)
    if removed_crops:
        print(
            f"[clean] Dropped {len(removed_crops)} rare crops "
            f"(< {MIN_SAMPLES_PER_CROP} samples): {removed_crops}  "
            f"({n_before - len(df):,} rows removed)"
        )

    # Step 2: Remove per-crop yield outliers (> OUTLIER_SIGMA σ from mean)
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
    df = df[keep_mask].reset_index(drop=True)
    print(f"[clean] Removed {n_before - len(df):,} yield outliers (> {OUTLIER_SIGMA}σ per crop).")

    # Step 3: Balance — cap at MAX_SAMPLES_PER_CROP rows per crop
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
    """Load source dataset, clean, train, evaluate, and save artefacts."""

    # ── Load ─────────────────────────────────────────────────────────────────
    if not os.path.exists(_DATASET_PATH):
        raise FileNotFoundError(
            f"Dataset not found: {_DATASET_PATH!r}\n"
            "Ensure 'Final_Agriculture_Dataset_ML_Final.csv' is present in the notebooks/ directory."
        )
    df = pd.read_csv(_DATASET_PATH)
    print(f"[load] {_DATASET_PATH}")
    print(f"       shape={df.shape}  crops={df[_LABEL_COL].nunique()}")

    # ── Rename source column names to internal names ──────────────────────────
    df = df.rename(columns={
        "N": "nitrogen",
        "P": "phosphorus",
        "K": "potassium",
        "Area": "area",
        "district_name": "district",
        "Season": "season",
    })

    # ── Clean: rare crops, outliers, balance ─────────────────────────────────
    df = _clean_dataset(df)

    # ── Add engineered features ───────────────────────────────────────────────
    df = _add_engineered_features(df)

    # ── Encode crop labels ────────────────────────────────────────────────────
    le = LabelEncoder()
    df["crop_encoded"] = le.fit_transform(df[_LABEL_COL].values)
    print(f"\nCrop classes ({len(le.classes_)}): {list(le.classes_)}")

    # ── Build feature matrices ────────────────────────────────────────────────
    feature_cols_crop = _BASE_FEATURES + _ENGINEERED_FEATURES
    feature_cols_yield = feature_cols_crop + ["crop_encoded"]

    X_crop = df[feature_cols_crop].values
    y_crop = df["crop_encoded"].values
    X_yield = df[feature_cols_yield].values
    y_yield = df[_YIELD_COL].values

    # ── Train / test split (BEFORE fitting any preprocessor) ─────────────────
    X_crop_train, X_crop_test, y_crop_train, y_crop_test = train_test_split(
        X_crop, y_crop,
        test_size=0.20, random_state=RANDOM_SEED, stratify=y_crop,
    )
    X_yield_train, X_yield_test, y_yield_train, y_yield_test = train_test_split(
        X_yield, y_yield,
        test_size=0.20, random_state=RANDOM_SEED,
    )
    print(f"\nTrain size: {len(X_crop_train):,} | Test size: {len(X_crop_test):,}")
    print(f"Crop features ({len(feature_cols_crop)}): {feature_cols_crop}")

    # =========================================================================
    # Crop Recommendation Model
    # Pipeline embeds the scaler so CV / inference are always leak-free.
    # =========================================================================
    print("\n" + "=" * 68)
    print("  Training Crop Recommendation Model")
    print("=" * 68)

    crop_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=300,
            max_depth=None,
            min_samples_leaf=1,
            max_features="sqrt",
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )),
    ])
    crop_pipeline.fit(X_crop_train, y_crop_train)

    train_acc = accuracy_score(y_crop_train, crop_pipeline.predict(X_crop_train))
    test_acc = accuracy_score(y_crop_test, crop_pipeline.predict(X_crop_test))
    print(f"  Train accuracy : {train_acc:.2%}")
    print(f"  Test  accuracy : {test_acc:.2%}")

    if test_acc < 0.90:
        print(f"  ⚠  Test accuracy {test_acc:.2%} is below the 90 % target.")

    cv_crop = cross_val_score(
        crop_pipeline, X_crop, y_crop,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED),
        scoring="accuracy", n_jobs=-1,
    )
    print(f"  5-Fold CV acc  : {cv_crop.round(4)} → mean={cv_crop.mean():.4f} ± {cv_crop.std():.4f}")

    print("\n  Classification report (test set):")
    print(
        classification_report(
            y_crop_test,
            crop_pipeline.predict(X_crop_test),
            target_names=le.classes_,
            zero_division=0,
        )
    )

    # =========================================================================
    # Yield Prediction Model
    # Scaler fitted on training split only; saved separately for inference.
    # =========================================================================
    print("=" * 68)
    print("  Training Yield Prediction Model")
    print("=" * 68)

    scaler_yield = StandardScaler()
    X_yield_train_sc = scaler_yield.fit_transform(X_yield_train)
    X_yield_test_sc = scaler_yield.transform(X_yield_test)

    yield_model = RandomForestRegressor(
        n_estimators=300,
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

    # CV for yield uses a Pipeline per fold to prevent leakage
    yield_cv_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("reg", RandomForestRegressor(
            n_estimators=300, max_depth=None, min_samples_leaf=2,
            max_features="sqrt", random_state=RANDOM_SEED, n_jobs=-1,
        )),
    ])
    cv_yield = cross_val_score(
        yield_cv_pipeline, X_yield, y_yield, cv=5, scoring="r2", n_jobs=-1,
    )
    print(f"  5-Fold CV R²   : {cv_yield.round(4)} → mean={cv_yield.mean():.4f} ± {cv_yield.std():.4f}")

    # ── Save artefacts ────────────────────────────────────────────────────────
    models_dir = os.path.join(_BACKEND_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)

    artefacts: dict = {
        "crop_model.pkl":    crop_pipeline,   # Pipeline: StandardScaler + RF
        "yield_model.pkl":   yield_model,
        "label_encoder.pkl": le,
        "scaler_yield.pkl":  scaler_yield,
        "feature_cols.pkl":  {
            "crop":  feature_cols_crop,
            "yield": feature_cols_yield,
        },
    }

    for filename, obj in artefacts.items():
        out_path = os.path.join(models_dir, filename)
        joblib.dump(obj, out_path)
        print(f"Saved: {out_path}")

    # Save metadata so CropPredictor.model_accuracy can return the real value
    meta = {
        "algorithm": "Pipeline(StandardScaler + RandomForestClassifier)",
        "train_accuracy": round(train_acc * 100, 4),
        "test_accuracy": round(test_acc * 100, 4),
        "cv_accuracy_mean": round(float(cv_crop.mean()) * 100, 4),
        "cv_accuracy_std": round(float(cv_crop.std()) * 100, 4),
        "n_classes": int(len(le.classes_)),
        "crop_classes": list(le.classes_),
        "feature_names": feature_cols_crop,
        "dataset": os.path.join("notebooks", "Final_Agriculture_Dataset_ML_Final.csv"),
        "random_seed": RANDOM_SEED,
    }
    meta_path = os.path.join(models_dir, "metadata.json")
    with open(meta_path, "w") as fh:
        json.dump(meta, fh, indent=2)
    print(f"Saved: {meta_path}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 68)
    print("  ✓ TRAINING COMPLETE — SUMMARY")
    print("=" * 68)
    print(f"  Dataset           : {_DATASET_PATH}")
    print(f"  Rows used         : {len(df):,}")
    print(f"  Crop classes      : {len(le.classes_)}")
    print(f"  Crop train acc    : {train_acc:.2%}")
    print(f"  Crop test acc     : {test_acc:.2%}")
    print(f"  Crop 5-fold CV    : {cv_crop.mean():.4f} ± {cv_crop.std():.4f}")
    print(f"  Yield 5-fold R²   : {cv_yield.mean():.4f} ± {cv_yield.std():.4f}")
    if test_acc >= 0.90:
        print("  ✓ Accuracy target (≥ 90 %) MET")
    else:
        print(f"  ✗ Accuracy target (≥ 90 %) NOT MET — see warnings above")
    print("=" * 68)


if __name__ == "__main__":
    train_and_save()
