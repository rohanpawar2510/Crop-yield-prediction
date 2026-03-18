"""
train_rf_from_dataset.py
========================
Train a Random Forest Regressor for crop yield prediction using the
crop recommendation dataset (``Crop_recommendation.csv``).

Usage
-----
    cd notebooks
    python train_rf_from_dataset.py [--dataset PATH] [--target COLUMN] [--output MODEL.pkl]

Arguments (all optional)
------------------------
--dataset   PATH to the CSV/Excel file.
            Defaults to searching the script's directory for
            "Crop_recommendation.csv".
--target    Name of the yield column to predict.
            Auto-detected if not provided.
--output    Path for the saved model .pkl file.
            Default: crop_yield_rf_model.pkl (in the script's directory).
"""

from __future__ import annotations

import argparse
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split

RANDOM_SEED = 42

# ── Candidate file names ───────────────────────────────────────────────────────
_CANDIDATE_NAMES = [
    "Crop_recommendation.csv",
    "crop_recommendation.csv",
    "final dataset encoding.csv",
    "final_dataset_encoding.csv",
    "final dataset encoding.xlsx",
    "final_dataset_encoding.xlsx",
]

# Common substrings that indicate the yield (target) column
_YIELD_KEYWORDS = ["yield", "production", "output", "hg/ha", "kg/ha", "tons"]


def _find_dataset(script_dir: str) -> str:
    """Return path to the dataset, searching common file names."""
    for name in _CANDIDATE_NAMES:
        path = os.path.join(script_dir, name)
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        "Dataset not found in {!r}. Place 'Crop_recommendation.csv' there or pass --dataset PATH.".format(script_dir)
    )


def _detect_target(df: pd.DataFrame) -> str:
    """Return the name of the yield/target column using keyword matching."""
    for col in df.columns:
        if any(kw in col.lower() for kw in _YIELD_KEYWORDS):
            return col
    # Fall back to the last numeric column
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        raise ValueError("No numeric columns found in the dataset.")
    last_col = numeric_cols[-1]
    print(
        f"[Warning] Could not auto-detect yield column — using last numeric column: '{last_col}'. "
        "Pass --target COLUMN_NAME to override."
    )
    return last_col


def load_data(path: str) -> pd.DataFrame:
    """Load CSV or Excel file into a DataFrame."""
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    print(f"Loaded dataset: {path} — shape {df.shape}")
    return df


def prepare_features(df: pd.DataFrame, target_col: str) -> tuple[pd.DataFrame, pd.Series]:
    """Return (X, y) keeping only numeric feature columns."""
    df_clean = df.dropna(subset=[target_col]).copy()
    dropped = len(df) - len(df_clean)
    if dropped:
        print(f"Dropped {dropped} rows with missing target values.")

    feature_cols = [c for c in df_clean.columns if c != target_col]
    numeric_cols = df_clean[feature_cols].select_dtypes(include=[np.number]).columns.tolist()
    non_numeric = [c for c in feature_cols if c not in numeric_cols]
    if non_numeric:
        print(f"[Info] Ignoring non-numeric columns: {non_numeric}")

    # Impute any remaining NaN with column median
    X = df_clean[numeric_cols].fillna(df_clean[numeric_cols].median())
    y = df_clean[target_col]

    print(f"Features : {X.shape[1]} columns — {list(X.columns)}")
    print(f"Target   : '{target_col}' — mean={y.mean():.4f}, std={y.std():.4f}")
    return X, y


def train(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestRegressor:
    """Fit and return a Random Forest Regressor."""
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        min_samples_leaf=2,
        max_features="sqrt",
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    print("Random Forest Regressor trained successfully.")
    return model


def evaluate(
    model: RandomForestRegressor,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> None:
    """Print train/test metrics and cross-validation R²."""
    def _metrics(y_true: pd.Series, y_pred: np.ndarray, label: str) -> None:
        r2   = r2_score(y_true, y_pred)
        mae  = mean_absolute_error(y_true, y_pred)
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        print(f"  {label:6s}  R²={r2:.4f}  MAE={mae:.4f}  RMSE={rmse:.4f}")

    print("\n=== Model Performance ===")
    _metrics(y_train, model.predict(X_train), "Train")
    _metrics(y_test,  model.predict(X_test),  "Test")

    cv = cross_val_score(model, X_train, y_train, cv=5, scoring="r2", n_jobs=-1)
    print(f"\n  5-Fold CV R²: {cv.round(4)} → mean={cv.mean():.4f} ± {cv.std():.4f}")


def print_feature_importances(
    model: RandomForestRegressor,
    feature_names: list[str],
    top_n: int = 20,
) -> None:
    """Print the top-N most important features."""
    importances = pd.Series(model.feature_importances_, index=feature_names)
    importances_sorted = importances.sort_values(ascending=False)
    print(f"\n=== Top {min(top_n, len(importances_sorted))} Feature Importances ===")
    print(importances_sorted.head(top_n).to_string())


def save_model(model: RandomForestRegressor, output_path: str, feature_names: list[str]) -> None:
    """Persist the model and its feature list to disk."""
    joblib.dump(model, output_path)
    print(f"\nModel saved to: {output_path}")

    features_path = os.path.splitext(output_path)[0] + "_features.txt"
    with open(features_path, "w") as f:
        f.write("\n".join(feature_names))
    print(f"Feature list saved to: {features_path}")


def main(argv: list[str] | None = None) -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))

    parser = argparse.ArgumentParser(description="Train a Random Forest for crop yield prediction.")
    parser.add_argument("--dataset", default=None, help="Path to the hot-encoded CSV/Excel file.")
    parser.add_argument("--target",  default=None, help="Name of the yield column to predict.")
    parser.add_argument(
        "--output",
        default=os.path.join(script_dir, "crop_yield_rf_model.pkl"),
        help="Output path for the saved model .pkl file.",
    )
    args = parser.parse_args(argv)

    # 1. Locate dataset
    dataset_path = args.dataset if args.dataset else _find_dataset(script_dir)

    # 2. Load
    df = load_data(dataset_path)

    # 3. Detect target
    target_col = args.target if args.target else _detect_target(df)
    print(f"Target column: '{target_col}'")

    # 4. Prepare features
    X, y = prepare_features(df, target_col)

    # 5. Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_SEED
    )
    print(f"Train: {len(X_train)} rows | Test: {len(X_test)} rows")

    # 6. Train
    model = train(X_train, y_train)

    # 7. Evaluate
    evaluate(model, X_train, y_train, X_test, y_test)

    # 8. Feature importances
    print_feature_importances(model, list(X.columns))

    # 9. Save
    save_model(model, args.output, list(X.columns))
    print("\nDone.")


if __name__ == "__main__":
    main()
