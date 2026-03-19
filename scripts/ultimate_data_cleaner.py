"""
ultimate_data_cleaner.py
========================
Aggressive data-cleaning pipeline for maximum model accuracy.

8-Step Cleaning Pipeline
-------------------------
1. Load & validate columns / types.
2. Remove all rows with null values.
3. Strict range validation (humidity 0-100 %, temp -10-50 °C, pH 4-9, …).
4. Remove crops with < MIN_SAMPLES_PER_CROP (default 100) samples.
5. Remove yield outliers beyond OUTLIER_SIGMA (default 2.5) standard
   deviations from the per-crop mean — more aggressive than the previous 3σ.
6. Balance the dataset: sample at most MAX_SAMPLES_PER_CROP (default 1000)
   rows per crop to reduce class imbalance.
7. Add five engineered features.
8. Save cleaned dataset to notebooks/Crop_recommendation_final.csv and print
   a comprehensive report.

Expected results
----------------
- Input  : ~30 000 rows, 37 crops
- Output : ~12 000–15 000 rows, 15–20 crops
- Balance: each crop has 750–1000 samples
- Quality: no nulls, no outliers, all features properly ranged

Usage
-----
    # From the repository root
    python scripts/ultimate_data_cleaner.py

    # Custom options
    python scripts/ultimate_data_cleaner.py \\
        --input  notebooks/Crop_recommendation.csv \\
        --output notebooks/Crop_recommendation_final.csv \\
        --min-samples 100 \\
        --max-samples 1000 \\
        --outlier-sigma 2.5
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Allow importing feature_engineering from the same package directory
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from feature_engineering import add_features  # noqa: E402

# ---------------------------------------------------------------------------
# Default configuration
# ---------------------------------------------------------------------------
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)

_DEFAULT_INPUT = os.path.join(_REPO_ROOT, "notebooks", "Crop_recommendation.csv")
_DEFAULT_OUTPUT = os.path.join(_REPO_ROOT, "notebooks", "Crop_recommendation_final.csv")

MIN_SAMPLES_PER_CROP: int = 100   # crops below this threshold are dropped
MAX_SAMPLES_PER_CROP: int = 1000  # hard cap per crop for class balance
OUTLIER_SIGMA: float = 2.5        # more aggressive than the previous 3σ

_LABEL_COL = "label"
_YIELD_COL = "yield"

# Strict agronomic ranges used in Step 3
_STRICT_RANGES: dict[str, tuple[float, float]] = {
    "N":           (0.0,   200.0),
    "P":           (0.0,   200.0),
    "K":           (0.0,   300.0),
    "temperature": (-10.0,  50.0),   # tighter upper bound than basic cleaner
    "humidity":    (0.0,   100.0),
    "ph":          (4.0,     9.0),   # agronomically meaningful range
    "rainfall":    (0.0,  3000.0),   # tighter upper bound
    "yield":       (0.0, 100000.0),
}

# Columns that must be present for the pipeline to proceed
_REQUIRED_COLS = list(_STRICT_RANGES.keys()) + [_LABEL_COL, _YIELD_COL]


# ---------------------------------------------------------------------------
# Step helpers
# ---------------------------------------------------------------------------

def _print_step(number: int, title: str) -> None:
    sep = "=" * 68
    print(f"\n{sep}")
    print(f"  STEP {number}: {title}")
    print(sep)


def _print_stat(label: str, value: object) -> None:
    print(f"  {label:<45s}: {value}")


# ---------------------------------------------------------------------------
# Step 1 – Load & validate
# ---------------------------------------------------------------------------

def _step1_load(path: str) -> pd.DataFrame:
    _print_step(1, "LOAD & VALIDATE")

    if not os.path.exists(path):
        print(f"[ERROR] Input file not found: {path!r}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(path)
    _print_stat("Input file", path)
    _print_stat("Rows loaded", f"{len(df):,}")
    _print_stat("Columns", list(df.columns))

    missing_cols = [c for c in _REQUIRED_COLS if c not in df.columns]
    if missing_cols:
        print(f"[ERROR] Missing required columns: {missing_cols}", file=sys.stderr)
        sys.exit(1)

    _print_stat("Crops (before cleaning)", df[_LABEL_COL].nunique())
    _print_stat("Null values (total)", int(df.isnull().sum().sum()))
    print("  ✓ All required columns present.")
    return df


# ---------------------------------------------------------------------------
# Step 2 – Remove nulls
# ---------------------------------------------------------------------------

def _step2_remove_nulls(df: pd.DataFrame) -> pd.DataFrame:
    _print_step(2, "REMOVE NULL VALUES")
    before = len(df)
    df = df.dropna(subset=_REQUIRED_COLS).reset_index(drop=True)
    removed = before - len(df)
    _print_stat("Rows before", f"{before:,}")
    _print_stat("Rows removed (nulls)", removed)
    _print_stat("Rows after", f"{len(df):,}")
    print("  ✓ No null values remain.")
    return df


# ---------------------------------------------------------------------------
# Step 3 – Strict range validation
# ---------------------------------------------------------------------------

def _step3_range_validation(df: pd.DataFrame) -> pd.DataFrame:
    _print_step(3, "STRICT RANGE VALIDATION")

    before = len(df)
    mask = pd.Series(True, index=df.index)

    for col, (lo, hi) in _STRICT_RANGES.items():
        if col not in df.columns:
            continue
        valid = df[col].between(lo, hi, inclusive="both")
        bad = (~valid).sum()
        if bad:
            _print_stat(f"  {col} out-of-range rows removed", bad)
        mask &= valid

    df = df[mask].reset_index(drop=True)
    removed = before - len(df)
    _print_stat("Rows before", f"{before:,}")
    _print_stat("Total out-of-range rows removed", removed)
    _print_stat("Rows after", f"{len(df):,}")
    print("  ✓ All values within strict agronomic ranges.")
    return df


# ---------------------------------------------------------------------------
# Step 4 – Remove crops with insufficient samples
# ---------------------------------------------------------------------------

def _step4_filter_crops(df: pd.DataFrame, min_samples: int) -> pd.DataFrame:
    _print_step(4, f"REMOVE CROPS WITH < {min_samples} SAMPLES")

    counts = df[_LABEL_COL].value_counts()
    dropped_crops = counts[counts < min_samples].index.tolist()

    if dropped_crops:
        _print_stat("Crops removed (< min samples)", sorted(dropped_crops))
    else:
        print("  All crops already have enough samples.")

    before_rows = len(df)
    df = df[~df[_LABEL_COL].isin(dropped_crops)].reset_index(drop=True)
    removed_rows = before_rows - len(df)

    _print_stat("Rows removed", removed_rows)
    _print_stat("Crops remaining", df[_LABEL_COL].nunique())
    _print_stat("Rows remaining", f"{len(df):,}")
    print(f"  ✓ Remaining crops: {sorted(df[_LABEL_COL].unique())}")
    return df


# ---------------------------------------------------------------------------
# Step 5 – Aggressive outlier removal (2.5σ)
# ---------------------------------------------------------------------------

def _step5_remove_outliers(df: pd.DataFrame, sigma: float) -> pd.DataFrame:
    _print_step(5, f"REMOVE YIELD OUTLIERS (> {sigma}σ per crop)")

    before = len(df)
    keep_mask = pd.Series(True, index=df.index)

    for crop, group in df.groupby(_LABEL_COL):
        yields = group[_YIELD_COL]
        mean_y = yields.mean()
        std_y = yields.std()
        if std_y == 0:
            continue
        outlier_mask = (yields - mean_y).abs() > sigma * std_y
        keep_mask.loc[group.index[outlier_mask]] = False

    df = df[keep_mask].reset_index(drop=True)
    removed = before - len(df)

    _print_stat("Rows before", f"{before:,}")
    _print_stat("Yield outliers removed", removed)
    _print_stat("Rows after", f"{len(df):,}")
    print(f"  ✓ All yield outliers beyond {sigma}σ removed.")
    return df


# ---------------------------------------------------------------------------
# Step 6 – Balance dataset (cap per crop)
# ---------------------------------------------------------------------------

def _step6_balance(df: pd.DataFrame, max_samples: int, random_state: int = 42) -> pd.DataFrame:
    _print_step(6, f"BALANCE DATASET (max {max_samples} samples per crop)")

    before = len(df)
    parts = []
    for crop, group in df.groupby(_LABEL_COL):
        if len(group) > max_samples:
            parts.append(group.sample(n=max_samples, random_state=random_state))
        else:
            parts.append(group)

    df = pd.concat(parts, ignore_index=True)
    df = df.sample(frac=1, random_state=random_state).reset_index(drop=True)

    _print_stat("Rows before", f"{before:,}")
    _print_stat("Rows after (balanced)", f"{len(df):,}")

    counts = df[_LABEL_COL].value_counts().sort_index()
    _print_stat("Samples per crop (min)", int(counts.min()))
    _print_stat("Samples per crop (max)", int(counts.max()))
    _print_stat("Samples per crop (mean)", f"{counts.mean():.0f}")
    print("  ✓ Dataset balanced.")
    return df


# ---------------------------------------------------------------------------
# Step 7 – Feature engineering
# ---------------------------------------------------------------------------

def _step7_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    _print_step(7, "FEATURE ENGINEERING")

    engineered = [
        "NPK_total",
        "NPK_ratio",
        "Climate_score",
        "Temp_humidity_interaction",
        "Soil_quality_score",
    ]
    already_present = [c for c in engineered if c in df.columns]
    if already_present:
        print(f"  Engineered features already present: {already_present}. Skipping.")
        return df

    df = add_features(df)

    for col in engineered:
        _print_stat(
            f"  {col}",
            f"mean={df[col].mean():.4f}  std={df[col].std():.4f}",
        )
    print("  ✓ 5 engineered features added.")
    return df


# ---------------------------------------------------------------------------
# Step 8 – Save & report
# ---------------------------------------------------------------------------

def _step8_save(df: pd.DataFrame, output_path: str) -> None:
    _print_step(8, "SAVE & FINAL REPORT")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    df.to_csv(output_path, index=False)

    _print_stat("Output file", output_path)
    _print_stat("Final shape", str(df.shape))
    _print_stat("Final rows", f"{len(df):,}")
    _print_stat("Final columns", df.shape[1])
    _print_stat("Crops in final dataset", df[_LABEL_COL].nunique())
    _print_stat("Null values (should be 0)", int(df.isnull().sum().sum()))

    print("\n  Crop distribution:")
    for crop, cnt in df[_LABEL_COL].value_counts().sort_index().items():
        bar = "█" * (cnt // 50)
        print(f"    {crop:<25s} {cnt:>5}  {bar}")

    print("\n  Yield statistics per crop:")
    stats = (
        df.groupby(_LABEL_COL)[_YIELD_COL]
        .agg(["count", "mean", "std", "min", "max"])
        .round(2)
    )
    print(stats.to_string())

    print(f"\n{'=' * 68}")
    print("  🎉  ULTIMATE DATA CLEANER COMPLETE!")
    print(f"{'=' * 68}")
    print(f"  ✓ Saved  : {output_path}")
    print(f"  ✓ Rows   : {len(df):,}")
    print(f"  ✓ Crops  : {df[_LABEL_COL].nunique()}")
    print(f"  ✓ Nulls  : {int(df.isnull().sum().sum())}")
    print()
    print("  Next step:")
    print("    cd backend && python train_models_final.py")
    print(f"{'=' * 68}\n")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_pipeline(
    input_path: str = _DEFAULT_INPUT,
    output_path: str = _DEFAULT_OUTPUT,
    min_samples: int = MIN_SAMPLES_PER_CROP,
    max_samples: int = MAX_SAMPLES_PER_CROP,
    outlier_sigma: float = OUTLIER_SIGMA,
) -> pd.DataFrame:
    """Execute all 8 cleaning steps and return the final DataFrame."""

    print("=" * 68)
    print("  ULTIMATE DATA CLEANER — Aggressive Filtering & Balancing")
    print("=" * 68)

    df = _step1_load(input_path)
    df = _step2_remove_nulls(df)
    df = _step3_range_validation(df)
    df = _step4_filter_crops(df, min_samples)
    df = _step5_remove_outliers(df, outlier_sigma)
    df = _step6_balance(df, max_samples)
    df = _step7_feature_engineering(df)
    _step8_save(df, output_path)

    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Aggressive 8-step data cleaning pipeline for maximum model accuracy.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--input",
        default=_DEFAULT_INPUT,
        help="Path to the input CSV file.",
    )
    p.add_argument(
        "--output",
        default=_DEFAULT_OUTPUT,
        help="Path to write the cleaned CSV file.",
    )
    p.add_argument(
        "--min-samples",
        type=int,
        default=MIN_SAMPLES_PER_CROP,
        dest="min_samples",
        help="Minimum samples required per crop (crops below this are dropped).",
    )
    p.add_argument(
        "--max-samples",
        type=int,
        default=MAX_SAMPLES_PER_CROP,
        dest="max_samples",
        help="Maximum samples per crop (for class balance).",
    )
    p.add_argument(
        "--outlier-sigma",
        type=float,
        default=OUTLIER_SIGMA,
        dest="outlier_sigma",
        help="Yield outlier threshold in standard deviations.",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_pipeline(
        input_path=args.input,
        output_path=args.output,
        min_samples=args.min_samples,
        max_samples=args.max_samples,
        outlier_sigma=args.outlier_sigma,
    )
