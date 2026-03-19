"""
data_analysis_report.py
=======================
Comprehensive data quality and exploratory analysis report for the crop
recommendation dataset.

Produces a printed report covering:
  - Dataset overview (shape, columns, dtypes)
  - Missing value audit
  - Feature range validation
  - Crop distribution (counts, % representation)
  - Yield statistics per crop (mean, std, min, max, IQR)
  - Outlier detection (values beyond ±3σ per crop)
  - Feature correlation matrix
  - Feature-to-label mutual information scores

Usage:
    python scripts/data_analysis_report.py
    python scripts/data_analysis_report.py --input notebooks/Crop_recommendation_improved.csv
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Default paths
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)
_DEFAULT_INPUT = os.path.join(_REPO_ROOT, "notebooks", "Crop_recommendation.csv")

_LABEL_COL = "label"
_YIELD_COL = "yield"

_NUMERIC_FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]

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

_SEP = "=" * 70
_SEP2 = "-" * 70


# ---------------------------------------------------------------------------
# Report sections
# ---------------------------------------------------------------------------

def _section(title: str) -> None:
    print(f"\n{_SEP}")
    print(f"  {title}")
    print(_SEP)


def report_overview(df: pd.DataFrame) -> None:
    _section("1. DATASET OVERVIEW")
    print(f"  Rows        : {len(df):,}")
    print(f"  Columns     : {len(df.columns)}")
    print(f"  Column names: {list(df.columns)}")
    print()
    print("  Data types:")
    for col in df.columns:
        print(f"    {col:<30s} {str(df[col].dtype)}")


def report_missing_values(df: pd.DataFrame) -> None:
    _section("2. MISSING VALUE AUDIT")
    nulls = df.isnull().sum()
    if nulls.sum() == 0:
        print("  ✓ No missing values found.")
    else:
        for col, cnt in nulls[nulls > 0].items():
            pct = cnt / len(df) * 100
            print(f"  {col:<30s} {cnt:>6,}  ({pct:.2f}%)")
    print(f"\n  Total null cells: {nulls.sum():,}")


def report_range_validation(df: pd.DataFrame) -> None:
    _section("3. FEATURE RANGE VALIDATION")
    all_ok = True
    for col, (lo, hi) in _VALID_RANGES.items():
        if col not in df.columns:
            print(f"  SKIP  {col:<20s} (column not present)")
            continue
        n_out = int(((df[col] < lo) | (df[col] > hi)).sum())
        status = "✓ OK  " if n_out == 0 else "✗ FAIL"
        val_min = df[col].min()
        val_max = df[col].max()
        print(
            f"  {status}  {col:<20s}  expected [{lo:.1f}, {hi:.1f}]  "
            f"actual [{val_min:.3f}, {val_max:.3f}]  "
            f"out-of-range={n_out}"
        )
        if n_out:
            all_ok = False
    print()
    print("  " + ("✓ All ranges valid." if all_ok else "✗ Some ranges invalid — see above."))


def report_crop_distribution(df: pd.DataFrame) -> None:
    _section("4. CROP DISTRIBUTION")
    counts = df[_LABEL_COL].value_counts().sort_values(ascending=False)
    total = len(df)
    print(f"  Total crops: {len(counts)}")
    print(f"  {'Crop':<25s} {'Count':>7}  {'%':>6}")
    print(f"  {_SEP2}")
    for crop, cnt in counts.items():
        pct = cnt / total * 100
        bar = "█" * int(pct / 2)
        print(f"  {crop:<25s} {cnt:>7,}  {pct:>5.1f}%  {bar}")

    print(f"\n  Min samples : {counts.min():,}  ({counts.idxmin()})")
    print(f"  Max samples : {counts.max():,}  ({counts.idxmax()})")
    print(f"  Median      : {counts.median():.0f}")

    underrep = counts[counts < 50]
    if len(underrep):
        print(f"\n  ⚠ Underrepresented crops (< 50 samples): {len(underrep)}")
        for crop, cnt in underrep.items():
            print(f"    {crop:<25s} {cnt}")


def report_yield_statistics(df: pd.DataFrame) -> None:
    _section("5. YIELD STATISTICS PER CROP")
    print(
        f"  {'Crop':<25s} {'Mean':>8} {'Std':>8} {'Min':>8} {'Max':>8} {'IQR':>8}"
    )
    print(f"  {_SEP2}")
    for crop, grp in sorted(df.groupby(_LABEL_COL)):
        y = grp[_YIELD_COL]
        q1, q3 = y.quantile(0.25), y.quantile(0.75)
        print(
            f"  {crop:<25s} "
            f"{y.mean():>8.1f} {y.std():>8.1f} "
            f"{y.min():>8.1f} {y.max():>8.1f} "
            f"{(q3 - q1):>8.1f}"
        )


def report_outliers(df: pd.DataFrame, sigma: float = 3.0) -> None:
    _section(f"6. OUTLIER DETECTION (±{sigma}σ per crop)")
    total_outliers = 0
    for crop, grp in sorted(df.groupby(_LABEL_COL)):
        y = grp[_YIELD_COL]
        mean, std = y.mean(), y.std(ddof=1)
        if std == 0:
            continue
        n_out = int(((y < mean - sigma * std) | (y > mean + sigma * std)).sum())
        pct = n_out / len(grp) * 100
        total_outliers += n_out
        flag = "  ⚠" if n_out else "   "
        print(f"{flag} {crop:<25s} n={len(grp):>5,}  outliers={n_out:>4,}  ({pct:.1f}%)")
    print(f"\n  Total outliers: {total_outliers:,}  ({total_outliers / len(df) * 100:.2f}% of dataset)")


def report_feature_correlation(df: pd.DataFrame) -> None:
    _section("7. FEATURE CORRELATION MATRIX")
    feat_cols = [c for c in _NUMERIC_FEATURES if c in df.columns]
    if _YIELD_COL in df.columns:
        feat_cols = feat_cols + [_YIELD_COL]

    corr = df[feat_cols].corr().round(3)

    # Print header
    header_cols = [f"{c[:8]:>9}" for c in feat_cols]
    print(f"  {'':16s}" + "".join(header_cols))
    print(f"  {_SEP2}")
    for idx in corr.index:
        row_vals = "".join(f"{v:>9.3f}" for v in corr.loc[idx])
        print(f"  {idx:<16s}{row_vals}")

    # Highlight strong correlations (|r| > 0.7), excluding self-correlation
    print("\n  Strong correlations (|r| > 0.70):")
    found = False
    for i, c1 in enumerate(feat_cols):
        for c2 in feat_cols[i + 1:]:
            r = corr.loc[c1, c2]
            if abs(r) > 0.70:
                print(f"    {c1} ↔ {c2}  r={r:.3f}")
                found = True
    if not found:
        print("    (none)")


def report_feature_importance(df: pd.DataFrame) -> None:
    _section("8. FEATURE-LABEL MUTUAL INFORMATION (crop classification)")
    try:
        from sklearn.feature_selection import mutual_info_classif
        from sklearn.preprocessing import LabelEncoder
    except ImportError:
        print("  scikit-learn not available — skipping MI analysis.")
        return

    feat_cols = [c for c in _NUMERIC_FEATURES if c in df.columns]
    X = df[feat_cols].values
    le = LabelEncoder()
    y = le.fit_transform(df[_LABEL_COL].values)

    mi = mutual_info_classif(X, y, random_state=42)
    order = np.argsort(mi)[::-1]

    print(f"  {'Feature':<30s} {'MI Score':>10}")
    print(f"  {_SEP2}")
    for idx in order:
        bar = "█" * int(mi[idx] * 40)
        print(f"  {feat_cols[idx]:<30s} {mi[idx]:>10.4f}  {bar}")


def report_data_validation_summary(df: pd.DataFrame) -> None:
    _section("9. DATA VALIDATION SUMMARY")
    checks = []

    # Null check
    null_total = df.isnull().sum().sum()
    checks.append(("No null values", null_total == 0, f"{null_total} null cells found"))

    # Range checks
    all_ranges_ok = True
    for col, (lo, hi) in _VALID_RANGES.items():
        if col not in df.columns:
            continue
        if ((df[col] < lo) | (df[col] > hi)).any():
            all_ranges_ok = False
            break
    checks.append(("All feature ranges valid", all_ranges_ok, "Some out-of-range values detected"))

    # Minimum crop representation
    min_count = df[_LABEL_COL].value_counts().min()
    checks.append((
        "All crops have ≥ 50 samples",
        min_count >= 50,
        f"Min crop count = {min_count}",
    ))

    # Dataset size
    enough_rows = len(df) >= 10_000
    checks.append(("Dataset has ≥ 10,000 rows", enough_rows, f"Only {len(df):,} rows"))

    for name, passed, detail in checks:
        icon = "✓" if passed else "✗"
        suffix = "" if passed else f"  ← {detail}"
        print(f"  {icon}  {name}{suffix}")

    passed_count = sum(1 for _, ok, _ in checks if ok)
    print(f"\n  Result: {passed_count}/{len(checks)} checks passed.")


# ---------------------------------------------------------------------------
# Top-level runner
# ---------------------------------------------------------------------------

def run_report(input_path: str) -> None:
    if not os.path.exists(input_path):
        print(f"[ERROR] File not found: {input_path!r}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(input_path)

    print(_SEP)
    print(f"  DATA ANALYSIS REPORT")
    print(f"  File : {input_path}")
    print(_SEP)

    report_overview(df)
    report_missing_values(df)
    report_range_validation(df)
    report_crop_distribution(df)
    report_yield_statistics(df)
    report_outliers(df)
    report_feature_correlation(df)
    report_feature_importance(df)
    report_data_validation_summary(df)

    print(f"\n{_SEP}")
    print("  END OF REPORT")
    print(_SEP + "\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument(
        "--input",
        default=_DEFAULT_INPUT,
        help="Path to the CSV file to analyse (default: notebooks/Crop_recommendation.csv).",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_report(args.input)
