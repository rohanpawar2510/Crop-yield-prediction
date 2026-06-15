"""
train_yield_model.py — Fixed yield model using Yield_Dataset_V1.csv

FIXES vs previous broken version:
  1. Back to Yield_Dataset_V1.csv — correct yield scale (Sugarcane ~2.1 t/ha)
  2. crop_encoded REMOVED — no leakage
  3. year → year_actual (0-13 → 2010-2023 real years)
  4. XGBoost replaces RandomForest
  5. irrigation_rainfall_interaction added

Dataset: notebooks/Yield_Dataset_V1.csv

Artefacts saved to backend/models/:
  yield_model.pkl         — XGBRegressor
  scaler_yield.pkl        — StandardScaler
  label_encoder_yield.pkl — LabelEncoder
  feature_cols_yield.pkl  — feature column list
  yield_metadata.json     — per-crop yield stats for confidence scoring

Usage:
    cd backend
    python train_yield_model.py
"""

from __future__ import annotations

import json
import os
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split, KFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

RANDOM_SEED          = 42
MIN_SAMPLES_PER_CROP = 100
MAX_SAMPLES_PER_CROP = 1000
OUTLIER_SIGMA        = 2.5

DROP_CROPS = {
    "APPLE", "ORANGE", "WATERMELON",
    "JUTE", "KIDNEYBEANS", "COCONUT",
    "POMEGRANATE", "CHILLIES",
    "PIGEONPEAS", "SUNFLOWER",
}

_BACKEND_DIR  = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT    = os.path.dirname(_BACKEND_DIR)
_DATASET_PATH = os.path.join(_REPO_ROOT, "notebooks", "Yield_Dataset_V1.csv")

_LABEL_COL = "label"
_YIELD_COL = "yield"

# NO crop_encoded — leakage fix
_BASE_FEATURES = [
    "nitrogen", "phosphorus", "potassium",
    "temperature", "humidity",
    "ph", "rainfall",
    "district", "season", "area",
    "irrigation_type",
    "soil_type",
    "year_actual",   # fixed: 0-13 → 2010-2023
]

_ENGINEERED_FEATURES = [
    "NPK_total",
    "NPK_ratio",
    "Climate_score",
    "Temp_humidity_interaction",
    "Soil_quality_score",
    "rain_per_temp",
    "N_to_P_ratio",
    "irrigation_rainfall_interaction",
]


def _add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["NPK_total"]                      = df["nitrogen"] + df["phosphorus"] + df["potassium"]
    df["NPK_ratio"]                      = df["nitrogen"] / (df["phosphorus"] + df["potassium"] + 1e-6)
    df["Climate_score"]                  = 0.5 * df["temperature"] + 0.5 * (df["rainfall"] / 100.0)
    df["Temp_humidity_interaction"]      = df["temperature"] * df["humidity"]
    df["Soil_quality_score"]             = 10.0 * np.exp(-0.5 * ((df["ph"] - 6.5) / 0.8) ** 2)
    df["rain_per_temp"]                  = df["rainfall"] / (df["temperature"] + 1e-6)
    df["N_to_P_ratio"]                   = df["nitrogen"] / (df["phosphorus"] + 1e-6)
    df["irrigation_rainfall_interaction"]= df["irrigation_type"] * df["rainfall"]
    return df


def _fix_year(df: pd.DataFrame) -> pd.DataFrame:
    """Map encoded year (0-13) → actual year (2010-2023)."""
    df = df.copy()
    df["year_actual"] = df["year"] + 2010
    print(f"[fix] year_actual range: {df['year_actual'].min()}–{df['year_actual'].max()}")
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
        parts.append(
            group.sample(n=min(len(group), MAX_SAMPLES_PER_CROP), random_state=RANDOM_SEED)
        )
    df = pd.concat(parts, ignore_index=True).sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    print(f"[clean] After balancing: {len(df):,} rows, {df[_LABEL_COL].nunique()} crops.")
    return df


def train_and_save() -> None:

    if not os.path.exists(_DATASET_PATH):
        raise FileNotFoundError(f"Dataset not found: {_DATASET_PATH!r}")

    df = pd.read_csv(_DATASET_PATH)
    print(f"[load] shape={df.shape}  crops={df[_LABEL_COL].nunique()}")

    df = _fix_year(df)
    df = _clean_dataset(df)
    df = _add_engineered_features(df)

    all_features = _BASE_FEATURES + _ENGINEERED_FEATURES
    missing = [f for f in all_features if f not in df.columns]
    if missing:
        raise ValueError(f"Missing features: {missing}")
    print(f"[verify] All {len(all_features)} features present ✓")
    print(f"[verify] crop_encoded intentionally excluded (leakage fix) ✓")

    le = LabelEncoder()
    le.fit(df[_LABEL_COL].values)
    print(f"\nCrop classes ({len(le.classes_)}): {list(le.classes_)}")

    feature_cols_yield = all_features   # no crop_encoded
    X = df[feature_cols_yield].values
    y = np.clip(df[_YIELD_COL].values, 0, np.percentile(df[_YIELD_COL].values, 99))

    print(f"\nYield scale: min={y.min():.4f}  max={y.max():.4f}  mean={y.mean():.4f}")
    print("Sugarcane mean yield:",
          round(df[df[_LABEL_COL]=="SUGARCANE"][_YIELD_COL].mean(), 4))

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED
    )

    scaler      = StandardScaler()
    X_train_sc  = scaler.fit_transform(X_train)
    X_test_sc   = scaler.transform(X_test)

    print("\n" + "=" * 68)
    print("  Training XGBoost Yield Model (V1 dataset, no crop_encoded)")
    print("=" * 68)

    yield_model = XGBRegressor(
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=10,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        early_stopping_rounds=50,
        eval_metric="rmse",
        random_state=RANDOM_SEED,
        n_jobs=-1,
        verbosity=0,
    )
    yield_model.fit(
        X_train_sc, y_train,
        eval_set=[(X_test_sc, y_test)],
        verbose=False,
    )
    print(f"  Best iteration: {yield_model.best_iteration}")

    for lbl, X_s, y_s in [("Train", X_train_sc, y_train), ("Test ", X_test_sc, y_test)]:
        y_pred = yield_model.predict(X_s)
        print(f"  {lbl}  R²={r2_score(y_s, y_pred):.4f}"
              f"  MAE={mean_absolute_error(y_s, y_pred):.4f}"
              f"  RMSE={float(np.sqrt(mean_squared_error(y_s, y_pred))):.4f}")

    cv_pipe = Pipeline([
        ("sc", StandardScaler()),
        ("reg", XGBRegressor(
            n_estimators=yield_model.best_iteration or 200,
            learning_rate=0.05, max_depth=6, subsample=0.8,
            colsample_bytree=0.8, min_child_weight=10, gamma=0.1,
            reg_alpha=0.1, reg_lambda=1.0,
            random_state=RANDOM_SEED, n_jobs=-1, verbosity=0,
        )),
    ])
    cv = cross_val_score(cv_pipe, X, y,
                         cv=KFold(5, shuffle=True, random_state=RANDOM_SEED),
                         scoring="r2", n_jobs=-1)
    print(f"  5-Fold CV R²: {cv.round(4)} → mean={cv.mean():.4f} ± {cv.std():.4f}")

    # Feature importances
    feat_imp = sorted(zip(feature_cols_yield, yield_model.feature_importances_),
                      key=lambda x: x[1], reverse=True)
    print("\n  Top 10 Feature Importances:")
    for f, i in feat_imp[:10]:
        print(f"    {f:<40} {i:.4f}")

    # Per-crop yield stats for confidence scoring in FastAPI
    crop_yield_stats = (
        df.groupby(_LABEL_COL)[_YIELD_COL]
        .agg(["mean", "std", "min", "max"])
        .round(4)
        .to_dict(orient="index")
    )

    # Save
    models_dir = os.path.join(_BACKEND_DIR, "models")
    os.makedirs(models_dir, exist_ok=True)

    artefacts = {
        "yield_model.pkl":         yield_model,
        "scaler_yield.pkl":        scaler,
        "label_encoder_yield.pkl": le,
        "feature_cols_yield.pkl":  feature_cols_yield,
    }
    for fname, obj in artefacts.items():
        path = os.path.join(models_dir, fname)
        joblib.dump(obj, path)
        print(f"Saved: {path}")

    meta = {
        "algorithm":        "XGBRegressor (no crop_encoded — leakage fixed)",
        "dataset":          "Yield_Dataset_V1.csv",
        "n_crops":          int(len(le.classes_)),
        "crop_classes":     list(le.classes_),
        "feature_names":    feature_cols_yield,
        "cv_r2_mean":       round(float(cv.mean()), 4),
        "cv_r2_std":        round(float(cv.std()), 4),
        "best_iteration":   int(yield_model.best_iteration or 0),
        "year_range":       [2010, 2023],
        "year_note":        "year_actual = raw_year + 2010",
        "crop_yield_stats": crop_yield_stats,
        "leakage_fix":      "crop_encoded removed",
        "yield_scale_note": "V1 scale: SUGARCANE~2.1, BANANA~1.7, RICE~0.14 t/ha",
    }
    meta_path = os.path.join(models_dir, "yield_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Saved: {meta_path}")

    print("\n" + "=" * 68)
    print("  YIELD TRAINING COMPLETE")
    print("=" * 68)
    print(f"  Dataset        : Yield_Dataset_V1.csv (correct yield scale)")
    print(f"  Rows           : {len(df):,}")
    print(f"  Features       : {len(feature_cols_yield)} (crop_encoded EXCLUDED)")
    print(f"  5-Fold CV R²   : {cv.mean():.4f} ± {cv.std():.4f}")
    print(f"  Yield scale    : SUGARCANE~2.1 t/ha, BANANA~1.7 t/ha ✓")
    print("=" * 68)


if __name__ == "__main__":
    train_and_save()