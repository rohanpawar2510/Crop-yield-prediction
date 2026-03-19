"""
feature_engineering.py
======================
Feature engineering utilities for the crop recommendation dataset.

Creates four additional features from the base soil/climate columns:

  - NPK_total               : N + P + K  (total nutrient load)
  - NPK_ratio               : N / (P + K + 1e-6)  (nitrogen balance)
  - Climate_score           : 0.4*temperature + 0.3*humidity + 0.3*(rainfall/100)
  - Temp_humidity_interaction: temperature * humidity
  - Soil_quality_score      : pH-based quality score (optimal range 6.0–7.0)

Usage (standalone):
    python feature_engineering.py
        --input  notebooks/Crop_recommendation.csv
        --output notebooks/Crop_recommendation_features.csv

Usage (as a library):
    from scripts.feature_engineering import add_features
    df_enriched = add_features(df)
"""

from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Core feature-engineering function
# ---------------------------------------------------------------------------

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of *df* with five new engineered columns appended.

    Parameters
    ----------
    df:
        DataFrame that must contain columns N, P, K, temperature,
        humidity, ph, and rainfall.

    Returns
    -------
    pd.DataFrame
        A new DataFrame (the original is never modified) with five extra
        columns: NPK_total, NPK_ratio, Climate_score,
        Temp_humidity_interaction, Soil_quality_score.
    """
    required = {"N", "P", "K", "temperature", "humidity", "ph", "rainfall"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input DataFrame is missing required columns: {missing}")

    out = df.copy()

    # 1. NPK_total — total nutrient load
    out["NPK_total"] = out["N"] + out["P"] + out["K"]

    # 2. NPK_ratio — nitrogen balance relative to secondary nutrients
    out["NPK_ratio"] = out["N"] / (out["P"] + out["K"] + 1e-6)

    # 3. Climate_score — weighted climate index
    out["Climate_score"] = (
        0.4 * out["temperature"]
        + 0.3 * out["humidity"]
        + 0.3 * (out["rainfall"] / 100.0)
    )

    # 4. Temp_humidity_interaction — combined water-temperature effect
    out["Temp_humidity_interaction"] = out["temperature"] * out["humidity"]

    # 5. Soil_quality_score — pH-based indicator (peak at pH 6.5, range 0–10)
    #    Uses a Gaussian centered at the agronomically optimal pH of 6.5
    out["Soil_quality_score"] = 10.0 * np.exp(-0.5 * ((out["ph"] - 6.5) / 0.8) ** 2)

    return out


# ---------------------------------------------------------------------------
# Standalone CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Add engineered features to a crop recommendation CSV."
    )
    p.add_argument(
        "--input",
        default=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "notebooks",
            "Crop_recommendation.csv",
        ),
        help="Path to the input CSV file.",
    )
    p.add_argument(
        "--output",
        default=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "notebooks",
            "Crop_recommendation_features.csv",
        ),
        help="Path to write the output CSV file.",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input!r}")

    print(f"Reading  : {args.input}")
    df = pd.read_csv(args.input)
    print(f"  Shape  : {df.shape}")

    df_out = add_features(df)
    new_cols = ["NPK_total", "NPK_ratio", "Climate_score", "Temp_humidity_interaction", "Soil_quality_score"]
    print(f"\nNew features added:")
    for col in new_cols:
        print(f"  {col:30s} mean={df_out[col].mean():.4f}  std={df_out[col].std():.4f}")

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    df_out.to_csv(args.output, index=False)
    print(f"\nSaved    : {args.output}  shape={df_out.shape}")


if __name__ == "__main__":
    main()
