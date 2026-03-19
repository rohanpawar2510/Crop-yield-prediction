#!/usr/bin/env python3
"""
add_humidity_to_csv.py

Reads ``notebooks/Crop_Final_Updated.csv`` (or ``Crop_Final_Updated (1).csv``),
fetches real-time humidity data from the OpenWeather API for each unique
Maharashtra district, adds a ``humidity`` column, reorders columns to the
structure expected by ``backend/train_models.py``, validates data quality, and
saves the result as ``notebooks/Crop_recommendation.csv``.

Usage
-----
    cd scripts
    python add_humidity_to_csv.py                      # estimation mode (no API key)
    python add_humidity_to_csv.py --api-key YOUR_KEY   # use OpenWeather API
    python add_humidity_to_csv.py --fallback-only      # force estimation mode

Environment variables (place in scripts/.env or set in shell):
    OPENWEATHER_API_KEY   OpenWeather API key (free tier is sufficient)
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT   = _SCRIPTS_DIR.parent
_NOTEBOOKS   = _REPO_ROOT / "notebooks"

# The source file may have a trailing "(1)" in its name
_POSSIBLE_INPUTS: List[Path] = [
    _NOTEBOOKS / "Crop_Final_Updated.csv",
    _NOTEBOOKS / "Crop_Final_Updated (1).csv",
]

OUTPUT_CSV = _NOTEBOOKS / "Crop_recommendation.csv"

# ---------------------------------------------------------------------------
# Column order expected by backend/train_models.py
# ---------------------------------------------------------------------------
OUTPUT_COLUMNS = [
    "district_name",
    "N",
    "P",
    "K",
    "temperature",
    "humidity",
    "ph",
    "rainfall",
    "label",
    "yield",
]

# ---------------------------------------------------------------------------
# Maharashtra district mapping  (dataset code → city name for OpenWeather)
# Covers district codes 25–60 used in the Maharashtra agricultural dataset
# ---------------------------------------------------------------------------
DISTRICT_MAP: Dict[int, str] = {
    25: "Pune,IN",
    26: "Nashik,IN",
    27: "Aurangabad,IN",
    28: "Amravati,IN",
    29: "Nagpur,IN",
    30: "Kolhapur,IN",
    31: "Sangli,IN",
    32: "Satara,IN",
    33: "Solapur,IN",
    34: "Ahmednagar,IN",
    35: "Jalgaon,IN",
    36: "Dhule,IN",
    37: "Nandurbar,IN",
    38: "Osmanabad,IN",
    39: "Latur,IN",
    40: "Nanded,IN",
    41: "Parbhani,IN",
    42: "Hingoli,IN",
    43: "Beed,IN",
    44: "Jalna,IN",
    45: "Buldhana,IN",
    46: "Akola,IN",
    47: "Washim,IN",
    48: "Yavatmal,IN",
    49: "Wardha,IN",
    50: "Bhandara,IN",
    51: "Gondia,IN",
    52: "Chandrapur,IN",
    53: "Gadchiroli,IN",
    54: "Raigad,IN",
    55: "Ratnagiri,IN",
    56: "Sindhudurg,IN",
    57: "Thane,IN",
    58: "Mumbai,IN",
    59: "Palghar,IN",
    60: "Nandurbar,IN",
}

# Default fallback city when a district code is not in the map
_DEFAULT_CITY = "Pune,IN"

# OpenWeather current-weather endpoint
_OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# ---------------------------------------------------------------------------
# Humidity estimation helpers
# ---------------------------------------------------------------------------

def _estimate_humidity(rainfall: float, temperature: float) -> float:
    """Estimate humidity (%) from rainfall (mm) and temperature (°C).

    Heuristic:
    - Base: 60 %
    - Each 30 mm of rainfall adds up to 25 percentage points
    - Each degree above 25 °C subtracts 0.5 percentage points
    Result is clamped to [20, 95].
    """
    base               = 60.0
    rain_contribution  = min(float(rainfall) / 30.0, 25.0)
    temp_contribution  = max((float(temperature) - 25.0) * -0.5, -15.0)
    estimated          = base + rain_contribution + temp_contribution
    return float(max(20.0, min(95.0, round(estimated, 1))))


def _district_fallback_humidity(df: pd.DataFrame, district: int) -> float:
    """Average estimated humidity across all rows belonging to *district*."""
    mask = df["district_name"] == district
    if not mask.any():
        return 65.0
    subset     = df.loc[mask, ["rainfall", "temperature"]]
    humidities = subset.apply(
        lambda r: _estimate_humidity(r["rainfall"], r["temperature"]), axis=1
    )
    return round(float(humidities.mean()), 1)


# ---------------------------------------------------------------------------
# OpenWeather API helper
# ---------------------------------------------------------------------------

def _fetch_humidity_api(city: str, api_key: str, timeout: int = 10) -> Optional[float]:
    """Fetch current humidity % for *city* from the OpenWeather API.

    Returns the humidity value (float, 0–100) or ``None`` on any failure.
    """
    try:
        response = requests.get(
            _OPENWEATHER_URL,
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=timeout,
        )
        response.raise_for_status()
        data     = response.json()
        humidity = data.get("main", {}).get("humidity")
        if humidity is not None:
            return float(humidity)
        log.warning("Unexpected API response for %s: %s", city, data)
    except requests.exceptions.HTTPError as exc:
        log.warning("HTTP error for %s: %s", city, exc)
    except requests.exceptions.ConnectionError:
        log.warning("Connection error — check network connectivity.")
    except requests.exceptions.Timeout:
        log.warning("Timeout fetching humidity for %s.", city)
    except Exception as exc:  # noqa: BLE001
        log.warning("Unexpected error for %s: %s", city, exc)
    return None


# ---------------------------------------------------------------------------
# Build per-district humidity cache
# ---------------------------------------------------------------------------

def build_humidity_cache(
    districts: List[int],
    df: pd.DataFrame,
    api_key: Optional[str] = None,
    rate_limit_seconds: float = 1.1,
) -> Dict[int, float]:
    """Return a dict mapping each district code to its humidity value (%).

    If *api_key* is provided the OpenWeather API is queried first; on failure
    (or when *api_key* is ``None``) the value is estimated from the district's
    average rainfall and temperature.
    """
    cache:   Dict[int, float] = {}
    use_api: bool             = bool(api_key)
    total                     = len(districts)

    log.info("Building humidity cache for %d unique district(s)…", total)
    if use_api:
        log.info("  Strategy: OpenWeather API  (fallback → estimation)")
    else:
        log.info("  Strategy: estimation from rainfall & temperature")

    for idx, district in enumerate(sorted(districts), start=1):
        city     = DISTRICT_MAP.get(int(district), _DEFAULT_CITY)
        fallback = _district_fallback_humidity(df, district)

        if use_api:
            log.info(
                "  [%d/%d] District %s (%s) — querying API…",
                idx, total, district, city,
            )
            api_value = _fetch_humidity_api(city, api_key)  # type: ignore[arg-type]
            if api_value is not None:
                log.info("          API      → %.1f %%", api_value)
                cache[district] = api_value
            else:
                log.info("          Estimate → %.1f %%", fallback)
                cache[district] = fallback
            time.sleep(rate_limit_seconds)   # respect free-tier rate limit
        else:
            log.info(
                "  [%d/%d] District %s — estimate → %.1f %%",
                idx, total, district, fallback,
            )
            cache[district] = fallback

    return cache


# ---------------------------------------------------------------------------
# Data validation
# ---------------------------------------------------------------------------

def validate_output(df: pd.DataFrame) -> bool:
    """Validate *df* against expected schema.  Returns ``True`` if all pass."""
    ok = True

    # Required columns present?
    missing_cols = [c for c in OUTPUT_COLUMNS if c not in df.columns]
    if missing_cols:
        log.error("Missing expected output columns: %s", missing_cols)
        ok = False

    # No null values
    null_counts = df.isnull().sum()
    if null_counts.any():
        log.error("Null values detected:\n%s", null_counts[null_counts > 0])
        ok = False
    else:
        log.info("✓  No null values")

    # Humidity range [20, 95]
    if "humidity" in df.columns:
        bad = df[(df["humidity"] < 20) | (df["humidity"] > 95)]
        if not bad.empty:
            log.error("Humidity out of range [20, 95]: %d row(s)", len(bad))
            ok = False
        else:
            log.info("✓  Humidity in valid range [20, 95]")

    # Numeric temperature
    if "temperature" in df.columns and not pd.api.types.is_numeric_dtype(df["temperature"]):
        log.error("'temperature' column is not numeric")
        ok = False

    # Positive yield
    if "yield" in df.columns:
        bad_yield = df[df["yield"] <= 0]
        if not bad_yield.empty:
            log.warning(
                "Non-positive 'yield' values found in %d row(s) — kept as-is.",
                len(bad_yield),
            )

    if ok:
        log.info("✓  All validation checks passed")
    return ok


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main(api_key: Optional[str] = None) -> None:
    # 1. Locate and load the source CSV
    source = next((p for p in _POSSIBLE_INPUTS if p.exists()), None)
    if source is None:
        log.error(
            "Source CSV not found.  Tried:\n  %s",
            "\n  ".join(str(p) for p in _POSSIBLE_INPUTS),
        )
        sys.exit(1)

    log.info("Reading  %s …", source)
    df = pd.read_csv(source)
    log.info("  Loaded  %d rows × %d columns", *df.shape)
    log.info("  Columns: %s", list(df.columns))

    # 2. Normalise column names to the expected schema
    rename_map = {
        "nitrogen":    "N",
        "phosphorus":  "P",
        "potassium":   "K",
        "Temperature": "temperature",
        "Rainfall":    "rainfall",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Validate that the label column is present
    if "label" not in df.columns:
        log.error("'label' column not found.  Available columns: %s", list(df.columns))
        sys.exit(1)

    # 3. Fetch or estimate humidity
    if "district_name" not in df.columns:
        log.warning(
            "'district_name' column not found — estimating humidity for every row individually."
        )
        df["humidity"] = df.apply(
            lambda r: _estimate_humidity(r["rainfall"], r["temperature"]), axis=1
        )
    else:
        unique_districts = sorted(df["district_name"].dropna().unique().tolist())
        humidity_cache   = build_humidity_cache(unique_districts, df, api_key=api_key)
        df["humidity"]   = df["district_name"].map(humidity_cache)

        # Fill any rows whose district was not in the cache (safety net)
        missing_mask = df["humidity"].isnull()
        if missing_mask.any():
            log.warning(
                "Estimating humidity for %d row(s) with unmapped district codes.",
                int(missing_mask.sum()),
            )
            df.loc[missing_mask, "humidity"] = df.loc[missing_mask].apply(
                lambda r: _estimate_humidity(r["rainfall"], r["temperature"]), axis=1
            )

    # 4. Select and reorder columns
    available = [c for c in OUTPUT_COLUMNS if c in df.columns]
    extra     = [c for c in df.columns if c not in OUTPUT_COLUMNS]
    if extra:
        log.info("Dropping %d extra column(s): %s", len(extra), extra)
    df = df[available]

    # 5. Validate
    log.info("\n--- Validation ---")
    valid = validate_output(df)

    # 6. Save output CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)

    log.info("\n✅  Saved  → %s", OUTPUT_CSV)
    log.info("   Shape  : %d rows × %d columns", *df.shape)
    log.info("   Columns: %s", list(df.columns))
    log.info("\nSample output:")
    log.info("\n%s", df.head(3).to_string(index=False))

    if not valid:
        log.warning("Output saved with validation warnings — review the errors above.")
        sys.exit(2)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Add humidity column to Crop_Final_Updated.csv and produce "
            "Crop_recommendation.csv in the notebooks/ folder."
        )
    )
    parser.add_argument(
        "--api-key",
        default=None,
        metavar="KEY",
        help="OpenWeather API key (overrides OPENWEATHER_API_KEY environment variable).",
    )
    parser.add_argument(
        "--fallback-only",
        action="store_true",
        help=(
            "Skip the OpenWeather API entirely; "
            "estimate humidity from rainfall & temperature."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    # Load scripts/.env if it exists and python-dotenv is available
    _env_file = _SCRIPTS_DIR / ".env"
    if _env_file.exists():
        try:
            from dotenv import load_dotenv  # type: ignore[import]
            load_dotenv(_env_file)
            log.info("Loaded environment from %s", _env_file)
        except ImportError:
            log.warning(
                "python-dotenv is not installed; skipping .env load.  "
                "Install it with: pip install python-dotenv"
            )

    # Resolve API key (CLI flag > env var)
    resolved_key: Optional[str] = None
    if not args.fallback_only:
        resolved_key = args.api_key or os.environ.get("OPENWEATHER_API_KEY")
        if not resolved_key:
            log.info(
                "OPENWEATHER_API_KEY not set — running in estimation (fallback) mode."
            )

    main(api_key=resolved_key)
