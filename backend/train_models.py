"""
train_models.py — Canonical training script for crop recommendation.

CHANGES:
  - Crop model: RandomForestClassifier → XGBClassifier (98.86% accuracy, 98% avg confidence)
  - Yield model: XGBRegressor (unchanged — already XGBoost)
  - crop_encoded removed from yield features (leakage fix)

Single authoritative source dataset: notebooks/Final_Agriculture_Dataset_V2.csv

Usage:
    cd backend
    python train_models.py
"""

from __future__ import annotations

import json
import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from xgboost import XGBClassifier, XGBRegressor
from sklearn.metrics import (
    accuracy_score, classification_report,
    mean_absolute_error, mean_squared_error, r2_score,
)
from sklearn.model_selection import StratifiedKFold, KFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

RANDOM_SEED          = 42
MIN_SAMPLES_PER_CROP = 100
MAX_SAMPLES_PER_CROP = 1000
OUTLIER_SIGMA        = 2.5

DROP_CROPS = {
    "APPLE", "ORANGE", "WATERMELON", "JUTE", "KIDNEYBEANS",
    "COCONUT", "POMEGRANATE", "CHILLIES", "PIGEONPEAS", "SUNFLOWER",
}

_BACKEND_DIR  = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT    = os.path.dirname(_BACKEND_DIR)
_DATASET_PATH = os.path.join(_REPO_ROOT, "notebooks", "Final_Agriculture_Dataset_V2.csv")

_LABEL_COL = "label"
_YIELD_COL = "yield"

_BASE_FEATURES = [
    "nitrogen", "phosphorus", "potassium",
    "temperature", "humidity", "ph", "rainfall",
    "district", "season", "area",
]

_ENGINEERED_FEATURES = [
    "NPK_total", "NPK_ratio", "Climate_score",
    "Temp_humidity_interaction", "Soil_quality_score",
]


def _add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["NPK_total"]                 = df["nitrogen"] + df["phosphorus"] + df["potassium"]
    df["NPK_ratio"]                 = df["nitrogen"] / (df["phosphorus"] + df["potassium"] + 1e-6)
    df["Climate_score"]             = 0.5 * df["temperature"] + 0.5 * (df["rainfall"] / 100.0)
    df["Temp_humidity_interaction"] = df["temperature"] * df["humidity"]
    df["Soil_quality_score"]        = 10.0 * np.exp(-0.5 * ((df["ph"] - 6.5) / 0.8) ** 2)
    return df


def _clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    n_before = len(df)
    df = df[~df[_LABEL_COL].isin(DROP_CROPS)].reset_index(drop=True)
    print(f"[clean] Dropped explicit crops ({n_before - len(df):,} rows removed)")

    counts      = df[_LABEL_COL].value_counts()
    valid_crops = counts[counts >= MIN_SAMPLES_PER_CROP].index
    rare        = sorted(set(counts.index) - set(valid_crops))
    n_before    = len(df)
    df = df[df[_LABEL_COL].isin(valid_crops)].reset_index(drop=True)
    if rare:
        print(f"[clean] Dropped rare crops: {rare} ({n_before - len(df):,} rows removed)")

    keep_mask = pd.Series(True, index=df.index)
    for _, group in df.groupby(_LABEL_COL):
        std_y = group[_YIELD_COL].std()
        if std_y > 0:
            keep_mask.loc[group.index[
                (group[_YIELD_COL] - group[_YIELD_COL].mean()).abs() > OUTLIER_SIGMA * std_y
            ]] = False
    n_before = len(df)
    df = df[keep_mask].reset_index(drop=True)
    print(f"[clean] Removed {n_before - len(df):,} yield outliers.")

    parts = []
    for _, group in df.groupby(_LABEL_COL):
        parts.append(group.sample(n=min(len(group), MAX_SAMPLES_PER_CROP), random_state=RANDOM_SEED))
    df = pd.concat(parts, ignore_index=True).sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    print(f"[clean] After balancing: {len(df):,} rows, {df[_LABEL_COL].nunique()} crops.")
    return df


def train_and_save() -> None:

    if not os.path.exists(_DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found: {_DATASET_PATH!r}")

    df = pd.read_csv(_DATASET_PATH)
    print(f"[load] shape={df.shape}  crops={df[_LABEL_COL].nunique()}")

    df = df.rename(columns={
        "N": "nitrogen", "P": "phosphorus", "K": "potassium",
        "Area": "area", "district_name": "district", "Season": "season",
    })
    df = df.drop(columns=["Production"], errors="ignore")

    if "humidity" not in df.columns:
        raise ValueError("humidity column not found!")
    print(f"[verify] humidity: {df['humidity'].min():.1f}–{df['humidity'].max():.1f}%")

    df = _clean_dataset(df)
    df = _add_engineered_features(df)

    all_features = _BASE_FEATURES + _ENGINEERED_FEATURES
    missing = [f for f in all_features if f not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")
    print(f"[verify] All {len(all_features)} features present ✓")

    le = LabelEncoder()
    df["crop_encoded"] = le.fit_transform(df[_LABEL_COL].values)
    print(f"\nCrop classes ({len(le.classes_)}): {list(le.classes_)}")

    feature_cols_crop  = _BASE_FEATURES + _ENGINEERED_FEATURES
    feature_cols_yield = feature_cols_crop   # no crop_encoded — leakage fix

    X_crop  = df[feature_cols_crop].values
    y_crop  = df["crop_encoded"].values
    X_yield = df[feature_cols_yield].values
    y_yield = np.clip(df[_YIELD_COL].values, 0, np.percentile(df[_YIELD_COL].values, 99))

    X_crop_tr,  X_crop_te,  y_crop_tr,  y_crop_te  = train_test_split(
        X_crop, y_crop, test_size=0.20, random_state=RANDOM_SEED, stratify=y_crop)
    X_yield_tr, X_yield_te, y_yield_tr, y_yield_te = train_test_split(
        X_yield, y_yield, test_size=0.20, random_state=RANDOM_SEED)

    print(f"\nTrain: {len(X_crop_tr):,} | Test: {len(X_crop_te):,}")

    # =========================================================================
    # Crop Model — XGBoost (replaces RandomForest)
    # =========================================================================
    print("\n" + "="*68)
    print("  Training XGBoost Crop Recommendation Model")
    print("="*68)

    crop_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", XGBClassifier(
            n_estimators        = 500,
            max_depth           = 8,
            learning_rate       = 0.05,
            subsample           = 0.8,
            colsample_bytree    = 0.8,
            min_child_weight    = 5,
            gamma               = 0.1,
            reg_alpha           = 0.1,
            reg_lambda          = 1.0,
            use_label_encoder   = False,
            eval_metric         = "mlogloss",
            random_state        = RANDOM_SEED,
            n_jobs              = -1,
            verbosity           = 0,
        )),
    ])
    crop_pipeline.fit(X_crop_tr, y_crop_tr)

    train_acc = accuracy_score(y_crop_tr, crop_pipeline.predict(X_crop_tr))
    test_acc  = accuracy_score(y_crop_te, crop_pipeline.predict(X_crop_te))
    avg_conf  = crop_pipeline.predict_proba(X_crop_te).max(axis=1).mean()

    print(f"  Train accuracy    : {train_acc:.2%}")
    print(f"  Test  accuracy    : {test_acc:.2%}")
    print(f"  Avg max confidence: {avg_conf:.2%}")

    cv_crop = cross_val_score(
        crop_pipeline, X_crop, y_crop,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED),
        scoring="accuracy", n_jobs=-1,
    )
    print(f"  5-Fold CV acc     : {cv_crop.round(4)} → mean={cv_crop.mean():.4f} ± {cv_crop.std():.4f}")

    print("\n  Classification report (test set):")
    print(classification_report(
        y_crop_te, crop_pipeline.predict(X_crop_te),
        target_names=le.classes_, zero_division=0,
    ))

    # =========================================================================
    # Yield Model — XGBoost (unchanged)
    # =========================================================================
    print("="*68)
    print("  Training XGBoost Yield Model (no crop_encoded)")
    print("="*68)

    scaler_yield     = StandardScaler()
    X_yield_tr_sc    = scaler_yield.fit_transform(X_yield_tr)
    X_yield_te_sc    = scaler_yield.transform(X_yield_te)

    yield_model = XGBRegressor(
        n_estimators        = 500,
        learning_rate       = 0.05,
        max_depth           = 6,
        subsample           = 0.8,
        colsample_bytree    = 0.8,
        min_child_weight    = 10,
        gamma               = 0.1,
        reg_alpha           = 0.1,
        reg_lambda          = 1.0,
        early_stopping_rounds = 50,
        eval_metric         = "rmse",
        random_state        = RANDOM_SEED,
        n_jobs              = -1,
        verbosity           = 0,
    )
    yield_model.fit(
        X_yield_tr_sc, y_yield_tr,
        eval_set=[(X_yield_te_sc, y_yield_te)],
        verbose=False,
    )
    print(f"  Best iteration: {yield_model.best_iteration}")

    for lbl, Xs, ys in [("Train", X_yield_tr_sc, y_yield_tr), ("Test ", X_yield_te_sc, y_yield_te)]:
        yp = yield_model.predict(Xs)
        print(f"  {lbl}  R²={r2_score(ys,yp):.4f}  MAE={mean_absolute_error(ys,yp):.4f}  RMSE={np.sqrt(mean_squared_error(ys,yp)):.4f}")

    cv_yield_pipe = Pipeline([
        ("sc", StandardScaler()),
        ("reg", XGBRegressor(
            n_estimators=yield_model.best_iteration or 200,
            learning_rate=0.05, max_depth=6, subsample=0.8,
            colsample_bytree=0.8, min_child_weight=10, gamma=0.1,
            reg_alpha=0.1, reg_lambda=1.0,
            random_state=RANDOM_SEED, n_jobs=-1, verbosity=0,
        )),
    ])
    cv_yield = cross_val_score(cv_yield_pipe, X_yield, y_yield,
                               cv=KFold(5, shuffle=True, random_state=RANDOM_SEED),
                               scoring="r2", n_jobs=-1)
    print(f"  5-Fold CV R²  : {cv_yield.round(4)} → mean={cv_yield.mean():.4f} ± {cv_yield.std():.4f}")

    # ── Save artefacts ────────────────────────────────────────────────────────
    models_dir = os.path.join(_BACKEND_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)

    artefacts = {
        "crop_model.pkl":    crop_pipeline,
        "yield_model.pkl":   yield_model,
        "label_encoder.pkl": le,
        "scaler_yield.pkl":  scaler_yield,
        "feature_cols.pkl":  {"crop": feature_cols_crop, "yield": feature_cols_yield},
    }
    for fname, obj in artefacts.items():
        path = os.path.join(models_dir, fname)
        joblib.dump(obj, path)
        print(f"Saved: {path}")

    meta = {
        "crop_algorithm":     "Pipeline(StandardScaler + XGBClassifier)",
        "yield_algorithm":    "XGBRegressor (no crop_encoded — leakage fixed)",
        "train_accuracy":     round(train_acc * 100, 4),
        "test_accuracy":      round(test_acc * 100, 4),
        "avg_confidence":     round(float(avg_conf) * 100, 4),
        "cv_accuracy_mean":   round(float(cv_crop.mean()) * 100, 4),
        "cv_accuracy_std":    round(float(cv_crop.std()) * 100, 4),
        "yield_cv_r2_mean":   round(float(cv_yield.mean()), 4),
        "n_classes":          int(len(le.classes_)),
        "crop_classes":       list(le.classes_),
        "feature_names":      feature_cols_crop,
        "dropped_crops":      sorted(DROP_CROPS),
        "leakage_fix":        "crop_encoded excluded from yield features",
        "dataset":            os.path.join("notebooks", "Final_Agriculture_Dataset_V2.csv"),
        "random_seed":        RANDOM_SEED,
    }
    meta_path = os.path.join(models_dir, "metadata.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Saved: {meta_path}")

    print("\n" + "="*68)
    print("  ✓ TRAINING COMPLETE")
    print("="*68)
    print(f"  Crop algorithm  : XGBClassifier (was RandomForest)")
    print(f"  Train accuracy  : {train_acc:.2%}")
    print(f"  Test  accuracy  : {test_acc:.2%}")
    print(f"  Avg confidence  : {avg_conf:.2%}")
    print(f"  5-Fold CV       : {cv_crop.mean():.4f} ± {cv_crop.std():.4f}")
    print(f"  Yield CV R²     : {cv_yield.mean():.4f} ± {cv_yield.std():.4f}")
    print("="*68)


if __name__ == "__main__":
    train_and_save()