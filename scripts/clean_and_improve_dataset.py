"""
clean_and_improve_dataset.py
============================
Data cleaning pipeline for the crop recommendation dataset.

Pipeline
--------
1. Load  notebooks/Crop_recommendation.csv and validate columns/types.
2. Remove underrepresented crops (< MIN_SAMPLES_PER_CROP = 50 samples).
3. Remove extreme yield outliers (values beyond ±3 standard deviations
   from the per-crop mean).
4. Validate that all feature values fall within expected agronomic ranges.
5. Apply feature engineering (NPK_total, NPK_ratio, Climate_score,
   Temp_humidity_interaction, Soil_quality_score).
6. Save cleaned dataset to notebooks/Crop_recommendation_improved.csv.

Usage:
    # From the repository root
    python scripts/clean_and_improve_dataset.py

    # Custom paths
    python scripts/clean_and_improve_dataset.py \\
        --input  notebooks/Crop_recommendation.csv \\
        --output notebooks/Crop_recommendation_improved.csv \\
        --min-samples 50 \\
        --outlier-sigma 3.0
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

# Make scripts/ importable as a package when running as a script
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from feature_engineering import add_features  # noqa: E402

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)
_DEFAULT_INPUT = os.path.join(_REPO_ROOT, "notebooks", "Crop_recommendation.csv")
_DEFAULT_OUTPUT = os.path.join(_REPO_ROOT, "notebooks", "Crop_recommendation_improved.csv")

MIN_SAMPLES_PER_CROP: int = 50
OUTLIER_SIGMA: float = 3.0

# Expected agronomic value ranges (inclusive) for validation
_VALID_RANGES: dict[str, tuple[float, float]] = {
    "N":           (0.0,   200.0),
    "P":           (0.0,   200.0),
    "K":           (0.0,   300.0),
    "temperature": (-10.0,  55.0),
    "humidity":    (0.0,   100.0),
    "ph":          (0.0,    14.0),
    "rainfall":    (0.0,  5000.0),
    "yield":       (0.0, 200000.0),
}

_LABEL_COL = "label"
_YIELD_COL = "yield"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _load(path: str) -> pd.DataFrame:
    """Load and basic-validate the input CSV."""
    if not os.path.exists(path):
        print(f"[ERROR] Input file not found: {path!r}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(path)
    print(f"[load]   {path}")
    print(f"         shape={df.shape}  crops={df[_LABEL_COL].nunique()}")

    required = list(_VALID_RANGES.keys()) + [_LABEL_COL, _YIELD_COL]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        print(f"[ERROR] Missing columns: {missing_cols}", file=sys.stderr)
        sys.exit(1)

    # Drop rows with any null in required columns
    before = len(df)
    df = df.dropna(subset=required).reset_index(drop=True)
    dropped = before - len(df)
    if dropped:
        print(f"[load]   Dropped {dropped} rows with null values.")

    return df


def _remove_undersampled_crops(df: pd.DataFrame, min_samples: int) -> pd.DataFrame:
    """Remove crops that have fewer than *min_samples* rows."""
    counts = df[_LABEL_COL].value_counts()
    keep_crops = counts[counts >= min_samples].index.tolist()
    removed_crops = sorted(set(counts.index) - set(keep_crops))

    before = len(df)
    df = df[df[_LABEL_COL].isin(keep_crops)].reset_index(drop=True)
    after = len(df)

    print(
        f"[filter] Removed {len(removed_crops)} undersampled crops "
        f"(< {min_samples} samples): {removed_crops}"
    )
    print(
        f"         Rows: {before} → {after}  "
        f"({before - after} rows removed)"
    )
    print(
        f"         Crops remaining ({len(keep_crops)}): "
        f"{sorted(keep_crops)}"
    )
    return df


def _remove_yield_outliers(df: pd.DataFrame, sigma: float) -> pd.DataFrame:
    """Remove rows where yield is beyond *sigma* std-devs from the per-crop mean."""
    mask = pd.Series(True, index=df.index)

    for crop, group in df.groupby(_LABEL_COL):
        mean = group[_YIELD_COL].mean()
        std = group[_YIELD_COL].std(ddof=1)
        if std == 0:
            continue
        lower = mean - sigma * std
        upper = mean + sigma * std
        crop_outliers = group.index[(group[_YIELD_COL] < lower) | (group[_YIELD_COL] > upper)]
        mask.loc[crop_outliers] = False

    before = len(df)
    df = df[mask].reset_index(drop=True)
    after = len(df)

    print(
        f"[outlier] Removed {before - after} yield outliers "
        f"(beyond ±{sigma}σ per crop).  "
        f"Rows: {before} → {after}"
    )
    return df


def _validate_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """Log and drop rows whose numeric features fall outside agronomic bounds."""
    mask = pd.Series(True, index=df.index)

    for col, (lo, hi) in _VALID_RANGES.items():
        if col not in df.columns:
            continue
        out_of_range = df.index[(df[col] < lo) | (df[col] > hi)]
        if len(out_of_range):
            print(
                f"[validate] {col}: {len(out_of_range)} values outside "
                f"[{lo}, {hi}] — dropped."
            )
            mask.loc[out_of_range] = False

    before = len(df)
    df = df[mask].reset_index(drop=True)
    if len(df) < before:
        print(f"[validate] Total out-of-range rows dropped: {before - len(df)}")
    else:
        print("[validate] All feature ranges valid ✓")
    return df


def _print_summary(df: pd.DataFrame, label: str = "") -> None:
    tag = f" ({label})" if label else ""
    print(f"\n{'='*60}")
    print(f"Dataset summary{tag}")
    print(f"{'='*60}")
    print(f"  Rows  : {len(df)}")
    print(f"  Cols  : {len(df.columns)} — {list(df.columns)}")
    print(f"  Crops : {df[_LABEL_COL].nunique()}")
    counts = df[_LABEL_COL].value_counts()
    for crop, cnt in counts.items():
        print(f"    {crop:<20s} {cnt:>5d}")
    print(f"  Yield stats  : mean={df[_YIELD_COL].mean():.1f}  "
          f"std={df[_YIELD_COL].std():.1f}  "
          f"max={df[_YIELD_COL].max():.1f}")
    print(f"  Null values  : {df.isnull().sum().sum()}")
    print()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def clean(
    input_path: str,
    output_path: str,
    min_samples: int = MIN_SAMPLES_PER_CROP,
    outlier_sigma: float = OUTLIER_SIGMA,
) -> pd.DataFrame:
    """Run the full cleaning pipeline and return the cleaned DataFrame."""
    print("\n" + "=" * 60)
    print("STEP 1 — Load & validate")
    print("=" * 60)
    df = _load(input_path)
    _print_summary(df, "original")

    print("=" * 60)
    print("STEP 2 — Remove underrepresented crops")
    print("=" * 60)
    df = _remove_undersampled_crops(df, min_samples)

    print("\n" + "=" * 60)
    print("STEP 3 — Remove yield outliers")
    print("=" * 60)
    df = _remove_yield_outliers(df, outlier_sigma)

    print("\n" + "=" * 60)
    print("STEP 4 — Validate feature ranges")
    print("=" * 60)
    df = _validate_ranges(df)

    print("\n" + "=" * 60)
    print("STEP 5 — Feature engineering")
    print("=" * 60)
    df = add_features(df)
    new_cols = [
        "NPK_total", "NPK_ratio", "Climate_score",
        "Temp_humidity_interaction", "Soil_quality_score",
    ]
    print(f"Added {len(new_cols)} new features: {new_cols}")

    _print_summary(df, "cleaned")

    print("=" * 60)
    print("STEP 6 — Save")
    print("=" * 60)
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved: {output_path}  shape={df.shape}")

    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--input", default=_DEFAULT_INPUT, help="Path to source CSV.")
    p.add_argument("--output", default=_DEFAULT_OUTPUT, help="Path for cleaned CSV.")
    p.add_argument(
        "--min-samples",
        type=int,
        default=MIN_SAMPLES_PER_CROP,
        help=f"Minimum samples per crop (default: {MIN_SAMPLES_PER_CROP}).",
    )
    p.add_argument(
        "--outlier-sigma",
        type=float,
        default=OUTLIER_SIGMA,
        help=f"Std-dev threshold for yield outlier removal (default: {OUTLIER_SIGMA}).",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    clean(
        input_path=args.input,
        output_path=args.output,
        min_samples=args.min_samples,
        outlier_sigma=args.outlier_sigma,
    )
