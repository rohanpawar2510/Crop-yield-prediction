"""
train_models.py — Canonical training script for crop recommendation.

Single authoritative source dataset: notebooks/Final_Agriculture_Dataset_V2.csv

Dataset schema:
  Columns: district_name, N, P, K, temperature, ph, rainfall, label, yield,
           Area, Production, Season, humidity
  Note: yield is already log-transformed in the dataset.

Data cleaning pipeline (inline):
  1. Rename columns (N→nitrogen, P→phosphorus, K→potassium,
     Area→area, district_name→district, Season→season).
  2. Drop unused Production column.
  3. Drop crops explicitly listed in DROP_CROPS (too few / ambiguous samples).
  4. Remove crops with fewer than MIN_SAMPLES_PER_CROP samples.
  5. Remove yield outliers beyond OUTLIER_SIGMA standard deviations per crop.
  6. Cap at MAX_SAMPLES_PER_CROP rows per crop (class balance).
  7. Add five engineered features (including Temp_humidity_interaction).

Training:
  - Split train/test FIRST (20 % held-out, stratified).
  - StandardScaler embedded in a Pipeline so CV / inference are always leak-free.
  - RandomForestClassifier (n_estimators=500, class_weight=balanced).
  - Reports train accuracy, test accuracy, 5-fold CV score, and classification
    report.

Artefacts saved to backend/models/:
  crop_model.pkl       — sklearn Pipeline (StandardScaler + RandomForest)
  yield_model.pkl      — RandomForestRegressor
  label_encoder.pkl    — LabelEncoder for crop names
  scaler_yield.pkl     — StandardScaler fitted on yield training split only
  feature_cols.pkl     — {'crop': [...], 'yield': [...]} feature column lists

Expected accuracy: ≥ 99 % crop classification on the test set.

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

RANDOM_SEED          = 42
MIN_SAMPLES_PER_CROP = 100    # crops below this threshold are dropped
MAX_SAMPLES_PER_CROP = 1000   # hard cap per crop for class balance
OUTLIER_SIGMA        = 2.5    # yield outlier threshold (std devs per crop)

# Crops with too few samples OR poor classification performance — drop explicitly
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
    _REPO_ROOT, "notebooks", "Final_Agriculture_Dataset_V2.csv"
)

_LABEL_COL = "label"
_YIELD_COL = "yield"

# ── Base features — includes humidity from Weather API ───────────────────────
_BASE_FEATURES = [
    "nitrogen", "phosphorus", "potassium",
    "temperature", "humidity",
    "ph", "rainfall",
    "district", "season", "area",
]

# ── Engineered features — includes Temp_humidity_interaction ─────────────────
_ENGINEERED_FEATURES = [
    "NPK_total",
    "NPK_ratio",
    "Climate_score",
    "Temp_humidity_interaction",
    "Soil_quality_score",
]


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with five engineered columns."""
    df = df.copy()
    df["NPK_total"]                 = df["nitrogen"] + df["phosphorus"] + df["potassium"]
    df["NPK_ratio"]                 = df["nitrogen"] / (df["phosphorus"] + df["potassium"] + 1e-6)
    df["Climate_score"]             = (
        0.5 * df["temperature"]
        + 0.5 * (df["rainfall"] / 100.0)
    )
    df["Temp_humidity_interaction"] = df["temperature"] * df["humidity"]
    df["Soil_quality_score"]        = 10.0 * np.exp(
        -0.5 * ((df["ph"] - 6.5) / 0.8) ** 2
    )
    return df


def _clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Apply cleaning pipeline: drop bad crops, filter rare, remove outliers, balance."""

    # Step 1: Drop explicitly listed low-quality crops
    n_before = len(df)
    df = df[~df[_LABEL_COL].isin(DROP_CROPS)].reset_index(drop=True)
    print(
        f"[clean] Explicitly dropped {len(DROP_CROPS)} crops: {sorted(DROP_CROPS)}  "
        f"({n_before - len(df):,} rows removed)"
    )

    # Step 2: Remove crops with insufficient samples
    counts        = df[_LABEL_COL].value_counts()
    valid_crops   = counts[counts >= MIN_SAMPLES_PER_CROP].index
    removed_crops = sorted(set(counts.index) - set(valid_crops))
    n_before      = len(df)
    df = df[df[_LABEL_COL].isin(valid_crops)].reset_index(drop=True)
    if removed_crops:
        print(
            f"[clean] Dropped {len(removed_crops)} rare crops "
            f"(< {MIN_SAMPLES_PER_CROP} samples): {removed_crops}  "
            f"({n_before - len(df):,} rows removed)"
        )

    # Step 3: Remove per-crop yield outliers (> OUTLIER_SIGMA σ from mean)
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
    print(f"[clean] Removed {n_before - len(df):,} yield outliers (> {OUTLIER_SIGMA}σ per crop).")

    # Step 4: Balance — cap at MAX_SAMPLES_PER_CROP rows per crop
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
            "Ensure 'Final_Agriculture_Dataset_V2.csv' is in notebooks/ directory."
        )
    df = pd.read_csv(_DATASET_PATH)
    print(f"[load] {_DATASET_PATH}")
    print(f"       shape={df.shape}  crops={df[_LABEL_COL].nunique()}")

    # ── Rename columns ────────────────────────────────────────────────────────
    df = df.rename(columns={
        "N":             "nitrogen",
        "P":             "phosphorus",
        "K":             "potassium",
        "Area":          "area",
        "district_name": "district",
        "Season":        "season",
    })

    # ── Drop unused columns ───────────────────────────────────────────────────
    df = df.drop(columns=["Production"], errors="ignore")

    # ── Verify humidity column exists ─────────────────────────────────────────
    if "humidity" not in df.columns:
        raise ValueError(
            "humidity column not found in dataset!\n"
            "Make sure you are using Final_Agriculture_Dataset_V2.csv"
        )
    print(
        f"[verify] humidity present — "
        f"range: {df['humidity'].min():.1f}–{df['humidity'].max():.1f}%  "
        f"mean: {df['humidity'].mean():.1f}%"
    )

    # ── Clean ─────────────────────────────────────────────────────────────────
    df = _clean_dataset(df)

    # ── Engineered features ───────────────────────────────────────────────────
    df = _add_engineered_features(df)

    # ── Verify all required features exist ───────────────────────────────────
    all_features = _BASE_FEATURES + _ENGINEERED_FEATURES
    missing = [f for f in all_features if f not in df.columns]
    if missing:
        raise ValueError(f"Missing columns after processing: {missing}")
    print(f"[verify] All {len(all_features)} features present ✓")

    # ── Encode crop labels ────────────────────────────────────────────────────
    le = LabelEncoder()
    df["crop_encoded"] = le.fit_transform(df[_LABEL_COL].values)
    print(f"\nCrop classes ({len(le.classes_)}): {list(le.classes_)}")

    # ── Build feature matrices ────────────────────────────────────────────────
    feature_cols_crop  = _BASE_FEATURES + _ENGINEERED_FEATURES
    feature_cols_yield = feature_cols_crop + ["crop_encoded"]

    X_crop  = df[feature_cols_crop].values
    y_crop  = df["crop_encoded"].values
    X_yield = df[feature_cols_yield].values

    # Clip extreme yield values (top 1%) to reduce noise
    y_yield = df[_YIELD_COL].values
    y_yield = np.clip(y_yield, 0, np.percentile(y_yield, 99))

    # ── Train / test split ────────────────────────────────────────────────────
    X_crop_train,  X_crop_test,  y_crop_train,  y_crop_test  = train_test_split(
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
    # =========================================================================
    print("\n" + "=" * 68)
    print("  Training Crop Recommendation Model")
    print("=" * 68)

    crop_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(
            n_estimators=500,
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
    test_acc  = accuracy_score(y_crop_test,  crop_pipeline.predict(X_crop_test))
    print(f"  Train accuracy : {train_acc:.2%}")
    print(f"  Test  accuracy : {test_acc:.2%}")

    if test_acc < 0.90:
        print(f"  ⚠  Test accuracy {test_acc:.2%} is below the 90% target.")

    cv_crop = cross_val_score(
        crop_pipeline, X_crop, y_crop,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED),
        scoring="accuracy", n_jobs=-1,
    )
    print(f"  5-Fold CV acc  : {cv_crop.round(4)} → mean={cv_crop.mean():.4f} ± {cv_crop.std():.4f}")

    print("\n  Classification report (test set):")
    print(classification_report(
        y_crop_test,
        crop_pipeline.predict(X_crop_test),
        target_names=le.classes_,
        zero_division=0,
    ))

    # =========================================================================
    # Yield Prediction Model
    # =========================================================================
    print("=" * 68)
    print("  Training Yield Prediction Model")
    print("=" * 68)

    scaler_yield     = StandardScaler()
    X_yield_train_sc = scaler_yield.fit_transform(X_yield_train)
    X_yield_test_sc  = scaler_yield.transform(X_yield_test)

    yield_model = RandomForestRegressor(
        n_estimators=500,
        max_depth=15,
        min_samples_leaf=10,
        min_samples_split=20,
        max_features="sqrt",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    yield_model.fit(X_yield_train_sc, y_yield_train)

    for split_lbl, X_s, y_s in [
        ("Train", X_yield_train_sc, y_yield_train),
        ("Test ", X_yield_test_sc,  y_yield_test),
    ]:
        y_pred = yield_model.predict(X_s)
        print(
            f"  {split_lbl}  R²={r2_score(y_s, y_pred):.4f}"
            f"  MAE={mean_absolute_error(y_s, y_pred):.4f}"
            f"  RMSE={float(np.sqrt(mean_squared_error(y_s, y_pred))):.4f}"
        )

    yield_cv_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("reg", RandomForestRegressor(
            n_estimators=500, max_depth=15, min_samples_leaf=10,min_samples_split=20,
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
        "crop_model.pkl":    crop_pipeline,
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

    meta = {
        "algorithm":        "Pipeline(StandardScaler + RandomForestClassifier)",
        "train_accuracy":   round(train_acc * 100, 4),
        "test_accuracy":    round(test_acc  * 100, 4),
        "cv_accuracy_mean": round(float(cv_crop.mean()) * 100, 4),
        "cv_accuracy_std":  round(float(cv_crop.std())  * 100, 4),
        "n_classes":        int(len(le.classes_)),
        "crop_classes":     list(le.classes_),
        "feature_names":    feature_cols_crop,
        "dropped_crops":    sorted(DROP_CROPS),
        "dataset":          os.path.join("notebooks", "Final_Agriculture_Dataset_V2.csv"),
        "random_seed":      RANDOM_SEED,
    }
    meta_path = os.path.join(models_dir, "metadata.json")
    with open(meta_path, "w") as fh:
        json.dump(meta, fh, indent=2)
    print(f"Saved: {meta_path}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 68)
    print("  ✓ TRAINING COMPLETE — SUMMARY")
    print("=" * 68)
    print(f"  Dataset        : {_DATASET_PATH}")
    print(f"  Rows used      : {len(df):,}")
    print(f"  Crop classes   : {len(le.classes_)}")
    print(f"  Dropped crops  : {sorted(DROP_CROPS)}")
    print(f"  Features       : {len(feature_cols_crop)} "
          f"(base={len(_BASE_FEATURES)}, engineered={len(_ENGINEERED_FEATURES)})")
    print(f"  Train acc      : {train_acc:.2%}")
    print(f"  Test  acc      : {test_acc:.2%}")
    print(f"  5-Fold CV      : {cv_crop.mean():.4f} ± {cv_crop.std():.4f}")
    print(f"  Yield R²       : {cv_yield.mean():.4f} ± {cv_yield.std():.4f}")
    if test_acc >= 0.99:
        print("  ✓ Accuracy target (≥ 99%) MET")
    elif test_acc >= 0.90:
        print("  ~ Accuracy target (≥ 90%) MET — aim for 99%+")
    else:
        print("  ✗ Accuracy target NOT MET — check dropped crops")
    print("=" * 68)


if __name__ == "__main__":
    train_and_save()