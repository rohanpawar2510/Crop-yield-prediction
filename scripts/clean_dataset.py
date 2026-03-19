"""
clean_dataset.py
================
Data cleaning pipeline: converts raw data_percentage.csv into the
production-ready crop_cleaned_v2.csv used for model training.

Input  : notebooks/data_percentage.csv  (raw dataset, 27 crops)
Output : notebooks/crop_cleaned_v2.csv  (14 columns, cleaned)

Output columns
--------------
district_name, N, P, K, temperature, ph, rainfall, label, yield,
NPK_total, recommended_crop, expected_yield, log_yield, log_expected_yield

Pipeline
--------
1.  Load raw CSV and validate required columns.
2.  Remove exact duplicate rows.
3.  Remove zero-yield rows (yield == 0).
4.  Per-crop IQR × 3 outlier removal on yield.
5.  Add NPK_total feature  (N + P + K).
6.  Add recommended_crop   (highest-median-yield crop per district).
7.  Add expected_yield     (median yield per crop + district).
8.  Add log_yield          (log1p of yield).
9.  Add log_expected_yield (log1p of expected_yield).
10. Validate data quality  (no nulls, positive yields).
11. Print summary statistics.

Usage
-----
    # From the repository root:
    python scripts/clean_dataset.py

    # Custom paths:
    python scripts/clean_dataset.py \\
        --input  notebooks/data_percentage.csv \\
        --output notebooks/crop_cleaned_v2.csv
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)

_DEFAULT_INPUT = os.path.join(_REPO_ROOT, "notebooks", "data_percentage.csv")
_DEFAULT_OUTPUT = os.path.join(_REPO_ROOT, "notebooks", "crop_cleaned_v2.csv")

# Required columns in the raw input CSV
_REQUIRED_COLS = ["district_name", "N", "P", "K", "temperature", "ph", "rainfall", "label", "yield"]

# IQR multiplier for outlier removal
_IQR_MULTIPLIER = 3.0


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

def _load(path: str) -> pd.DataFrame:
    """Load and basic-validate the raw CSV."""
    if not os.path.exists(path):
        print(f"[ERROR] Input file not found: {path!r}", file=sys.stderr)
        print("        Please upload data_percentage.csv to the notebooks/ directory.", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(path)
    print(f"[load]  {path}")
    print(f"        shape={df.shape}  crops={df['label'].nunique()}")

    missing_cols = [c for c in _REQUIRED_COLS if c not in df.columns]
    if missing_cols:
        print(f"[ERROR] Missing required columns: {missing_cols}", file=sys.stderr)
        sys.exit(1)

    return df


def _remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Step 1 — Remove exact duplicate rows."""
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    removed = before - len(df)
    print(f"[step1] Remove exact duplicates: {removed} removed → {len(df)} rows remain")
    return df


def _remove_zero_yield(df: pd.DataFrame) -> pd.DataFrame:
    """Step 2 — Remove rows where yield is zero or negative."""
    before = len(df)
    df = df[df["yield"] > 0].reset_index(drop=True)
    removed = before - len(df)
    print(f"[step2] Remove zero/negative-yield rows: {removed} removed → {len(df)} rows remain")
    return df


def _remove_iqr_outliers(df: pd.DataFrame, multiplier: float = _IQR_MULTIPLIER) -> pd.DataFrame:
    """Step 3 — Per-crop IQR × multiplier outlier removal on yield."""
    keep_mask = pd.Series(True, index=df.index)
    for crop, grp in df.groupby("label"):
        q1 = grp["yield"].quantile(0.25)
        q3 = grp["yield"].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - multiplier * iqr
        upper = q3 + multiplier * iqr
        outlier_idx = grp.index[(grp["yield"] < lower) | (grp["yield"] > upper)]
        keep_mask.loc[outlier_idx] = False

    before = len(df)
    df = df[keep_mask].reset_index(drop=True)
    removed = before - len(df)
    print(
        f"[step3] Per-crop IQR×{multiplier} outlier removal: "
        f"{removed} removed → {len(df)} rows remain"
    )
    return df


def _add_npk_total(df: pd.DataFrame) -> pd.DataFrame:
    """Step 4 — Add NPK_total = N + P + K."""
    df = df.copy()
    df["NPK_total"] = df["N"] + df["P"] + df["K"]
    print("[step4] Added NPK_total (N + P + K)")
    return df


def _add_recommended_crop(df: pd.DataFrame) -> pd.DataFrame:
    """Step 5 — Add recommended_crop: highest-median-yield crop per district."""
    df = df.copy()
    # Compute median yield per (district, crop)
    med = (
        df.groupby(["district_name", "label"])["yield"]
        .median()
        .reset_index()
        .rename(columns={"yield": "_med_yield"})
    )
    # For each district, pick the crop with the highest median yield
    best = (
        med.loc[med.groupby("district_name")["_med_yield"].idxmax()]
        .rename(columns={"label": "recommended_crop"})
        [["district_name", "recommended_crop"]]
    )
    df = df.merge(best, on="district_name", how="left")
    rec_nunique = df["recommended_crop"].nunique()
    print(f"[step5] Added recommended_crop ({rec_nunique} unique values)")
    return df


def _add_expected_yield(df: pd.DataFrame) -> pd.DataFrame:
    """Step 6 — Add expected_yield: median yield per (crop, district)."""
    df = df.copy()
    med = (
        df.groupby(["label", "district_name"])["yield"]
        .median()
        .reset_index()
        .rename(columns={"yield": "expected_yield"})
    )
    df = df.merge(med, on=["label", "district_name"], how="left")
    print(f"[step6] Added expected_yield (median yield per crop+district)")
    return df


def _add_log_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Steps 7-8 — Add log_yield and log_expected_yield using log1p."""
    df = df.copy()
    df["log_yield"] = np.log1p(df["yield"])
    df["log_expected_yield"] = np.log1p(df["expected_yield"])
    print("[step7] Added log_yield and log_expected_yield (log1p)")
    return df


def _select_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only the 14 production-ready columns in the specified order."""
    output_cols = [
        "district_name", "N", "P", "K", "temperature", "ph", "rainfall",
        "label", "yield", "NPK_total",
        "recommended_crop", "expected_yield", "log_yield", "log_expected_yield",
    ]
    missing = [c for c in output_cols if c not in df.columns]
    if missing:
        print(f"[ERROR] Output columns missing after pipeline: {missing}", file=sys.stderr)
        sys.exit(1)
    return df[output_cols].reset_index(drop=True)


def _validate(df: pd.DataFrame) -> None:
    """Step 8 — Validate data quality."""
    print("\n[validate] Running quality checks …")
    errors = []

    null_count = int(df.isnull().sum().sum())
    if null_count:
        errors.append(f"  ✗  {null_count} null values detected")
    else:
        print("  ✓  No null values")

    if (df["yield"] <= 0).any():
        errors.append("  ✗  Non-positive yield values detected")
    else:
        print("  ✓  All yield values > 0")

    if (df["log_yield"] < 0).any():
        errors.append("  ✗  Negative log_yield values (unexpected for yield > 0)")
    else:
        print("  ✓  All log_yield values ≥ 0")

    if df["recommended_crop"].isnull().any():
        errors.append("  ✗  Null values in recommended_crop")
    else:
        print(f"  ✓  recommended_crop: {df['recommended_crop'].nunique()} unique crops")

    if errors:
        print("\n[validate] FAILED:")
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(1)

    print("[validate] All checks passed ✓")


def _print_summary(df: pd.DataFrame) -> None:
    """Step 9 — Print summary statistics."""
    print("\n" + "=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print(f"  Rows               : {len(df):,}")
    print(f"  Columns            : {len(df.columns)}  {df.columns.tolist()}")
    print(f"  Crop classes       : {df['label'].nunique()}")
    print(f"  Recommended crops  : {df['recommended_crop'].nunique()}")
    print(f"  Districts          : {df['district_name'].nunique()}")
    print()
    print("  Crop distribution:")
    counts = df["label"].value_counts()
    for crop, cnt in counts.items():
        print(f"    {crop:<25s} {cnt:>6d}")
    print()
    print("  Yield statistics:")
    stats = df["yield"].describe()
    print(f"    min={stats['min']:.2f}  max={stats['max']:.2f}  "
          f"mean={stats['mean']:.2f}  median={df['yield'].median():.2f}  "
          f"std={stats['std']:.2f}")
    print()


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def clean(input_path: str, output_path: str) -> pd.DataFrame:
    """Run the full cleaning pipeline and save the result."""
    print("\n" + "=" * 60)
    print("CROP DATASET CLEANING PIPELINE")
    print("=" * 60)
    print(f"  Input  : {input_path}")
    print(f"  Output : {output_path}")
    print("=" * 60 + "\n")

    df = _load(input_path)
    df = _remove_duplicates(df)
    df = _remove_zero_yield(df)
    df = _remove_iqr_outliers(df)
    df = _add_npk_total(df)
    df = _add_recommended_crop(df)
    df = _add_expected_yield(df)
    df = _add_log_targets(df)
    df = _select_output_columns(df)
    _validate(df)
    _print_summary(df)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[save]  {output_path}  shape={df.shape}")

    return df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--input",
        default=_DEFAULT_INPUT,
        help=f"Path to raw input CSV (default: {_DEFAULT_INPUT})",
    )
    p.add_argument(
        "--output",
        default=_DEFAULT_OUTPUT,
        help=f"Path for cleaned output CSV (default: {_DEFAULT_OUTPUT})",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    clean(input_path=args.input, output_path=args.output)
