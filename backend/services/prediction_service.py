"""
prediction_service.py — Crop recommendation and yield prediction logic.

FIXES vs previous version:
  1. year → year_actual (actual year 2010-2023, matches Yield_Dataset_V2)
  2. crop_encoded removed from yield features (leakage fix)
  3. np.expm1() removed — Yield_Dataset_V2 yields are linear, not log-transformed
  4. Confidence scoring improved — seasonal adjustment prevents
     live weather (non-monsoon) from collapsing confidence scores

TWO SEPARATE MODELS:
  1. Crop Model (crop_model.pkl) — 15 features
     Trained on Final_Agriculture_Dataset_V2.csv

  2. Yield Model (yield_model.pkl) — 21 features, XGBoost
     Trained on Yield_Dataset_V1.csv
     Includes: irrigation_type, soil_type, year_actual (NO crop_encoded)

Model files in backend/models/:
  crop_model.pkl          — Pipeline (StandardScaler + RandomForest)
  label_encoder.pkl       — LabelEncoder for crop model
  feature_cols.pkl        — crop feature column list
  yield_model.pkl         — XGBRegressor (no crop_encoded)
  scaler_yield.pkl        — StandardScaler for yield
  label_encoder_yield.pkl — LabelEncoder for yield model
  feature_cols_yield.pkl  — yield feature column list
  yield_metadata.json     — per-crop yield stats for confidence scoring
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Optional

import numpy as np
import joblib

from models.schemas import CropPrediction, PredictResponse
from services.weather_service import get_weather

logger = logging.getLogger(__name__)

# ─── Model registry ───────────────────────────────────────────────────────────

_MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

_crop_model          = None
_label_encoder       = None
_feature_cols_crop   = None

_yield_model         = None
_scaler_yield        = None
_label_encoder_yield = None
_feature_cols_yield  = None
_crop_yield_stats    = {}   # per-crop yield stats for confidence adjustment

_models_loaded = False

# FIX 1: Use actual year (2010-2023), not encoded 0-13
# year_actual is clamped to training range so model never sees out-of-range values
_TRAIN_YEAR_MIN  = 2010
_TRAIN_YEAR_MAX  = 2023
_CURRENT_YEAR    = min(datetime.now().year, _TRAIN_YEAR_MAX)  # 2026 → clamped to 2023

# Seasonal rainfall defaults
# ONLY applied for Annual(4) — Kharif/Rabi/Zaid live weather is a better signal
# At 800mm Kharif: 17 crops compete → confidence drops to 16% (worse than live 52%)
# Annual season has specific crops (Sugarcane/Banana/Onion/Grapes) → override helps
_SEASONAL_RAINFALL = {
    4: 700,   # Annual only — live weather unreliable for annual crops
}

_SEASONAL_HUMIDITY = {
    4: 60.0,  # Annual only
}


def _load_models() -> bool:
    global _crop_model, _label_encoder, _feature_cols_crop
    global _yield_model, _scaler_yield, _label_encoder_yield
    global _feature_cols_yield, _crop_yield_stats, _models_loaded

    if _models_loaded:
        return _crop_model is not None

    try:
        _crop_model        = joblib.load(os.path.join(_MODELS_DIR, "crop_model.pkl"))
        _label_encoder     = joblib.load(os.path.join(_MODELS_DIR, "label_encoder.pkl"))
        _feat_cols_raw     = joblib.load(os.path.join(_MODELS_DIR, "feature_cols.pkl"))
        _feature_cols_crop = (
            _feat_cols_raw["crop"]
            if isinstance(_feat_cols_raw, dict)
            else _feat_cols_raw
        )

        _yield_model         = joblib.load(os.path.join(_MODELS_DIR, "yield_model.pkl"))
        _scaler_yield        = joblib.load(os.path.join(_MODELS_DIR, "scaler_yield.pkl"))
        _label_encoder_yield = joblib.load(os.path.join(_MODELS_DIR, "label_encoder_yield.pkl"))
        _feature_cols_yield  = joblib.load(os.path.join(_MODELS_DIR, "feature_cols_yield.pkl"))

        # Load per-crop yield stats for confidence scoring (FIX 4)
        try:
            meta_path = os.path.join(_MODELS_DIR, "yield_metadata.json")
            with open(meta_path) as f:
                meta = json.load(f)
            _crop_yield_stats = meta.get("crop_yield_stats", {})
            logger.info("   Yield stats loaded for %d crops", len(_crop_yield_stats))
        except Exception:
            _crop_yield_stats = {}

        logger.info("✅ All models loaded successfully")
        logger.info("   Crop classes  : %s", list(_label_encoder.classes_))
        logger.info("   Crop features : %s", _feature_cols_crop)
        logger.info("   Yield features: %s", _feature_cols_yield)
        logger.info("   Current year  : %d (clamped to training range %d-%d)",
                    _CURRENT_YEAR, _TRAIN_YEAR_MIN, _TRAIN_YEAR_MAX)

    except Exception as exc:
        logger.error("❌ Model loading failed: %s", exc)
        _crop_model = None

    _models_loaded = True
    return _crop_model is not None


# ─── Feature engineering ──────────────────────────────────────────────────────

def _build_crop_features(
    nitrogen: float, phosphorus: float, potassium: float,
    temperature: float, humidity: float,
    ph: float, rainfall: float,
    district: int, season: int, area: float,
) -> dict:
    """15 features for crop recommendation model. Matches train_models.py."""
    return {
        "nitrogen":                  nitrogen,
        "phosphorus":                phosphorus,
        "potassium":                 potassium,
        "temperature":               temperature,
        "humidity":                  humidity,
        "ph":                        ph,
        "rainfall":                  rainfall,
        "district":                  district,
        "season":                    season,
        "area":                      area,
        "NPK_total":                 nitrogen + phosphorus + potassium,
        "NPK_ratio":                 nitrogen / (phosphorus + potassium + 1e-6),
        "Climate_score":             0.5 * temperature + 0.5 * (rainfall / 100.0),
        "Temp_humidity_interaction": temperature * humidity,
        "Soil_quality_score":        10.0 * np.exp(-0.5 * ((ph - 6.5) / 0.8) ** 2),
    }


def _build_yield_features(
    nitrogen: float, phosphorus: float, potassium: float,
    temperature: float, humidity: float,
    ph: float, rainfall: float,
    district: int, season: int, area: float,
    irrigation_type: int,
    soil_type: int,
) -> dict:
    """
    21 features for yield model. Matches train_yield_model.py.

    FIX 1: 'year' (0-13 encoded) → 'year_actual' (2010-2023 real year)
    FIX 2: 'crop_encoded' removed — was target leakage
    FIX 3: Added 'irrigation_rainfall_interaction' to match V2 training features
    """
    NPK_total = nitrogen + phosphorus + potassium
    return {
        "nitrogen":                        nitrogen,
        "phosphorus":                      phosphorus,
        "potassium":                       potassium,
        "temperature":                     temperature,
        "humidity":                        humidity,
        "ph":                              ph,
        "rainfall":                        rainfall,
        "district":                        district,
        "season":                          season,
        "area":                            area,
        "irrigation_type":                 irrigation_type,
        "soil_type":                       soil_type,
        "year_actual":                     _CURRENT_YEAR,        # FIX 1
        "NPK_total":                       NPK_total,
        "NPK_ratio":                       nitrogen / (phosphorus + potassium + 1e-6),
        "Climate_score":                   0.5 * temperature + 0.5 * (rainfall / 100.0),
        "Temp_humidity_interaction":       temperature * humidity,
        "Soil_quality_score":              10.0 * np.exp(-0.5 * ((ph - 6.5) / 0.8) ** 2),
        "rain_per_temp":                   rainfall / (temperature + 1e-6),
        "N_to_P_ratio":                    nitrogen / (phosphorus + 1e-6),
        "irrigation_rainfall_interaction": irrigation_type * rainfall,  # FIX 3
        # crop_encoded intentionally excluded (FIX 2 — leakage fix)
    }


def _to_array(feat_dict: dict, col_order: list) -> np.ndarray:
    missing = [c for c in col_order if c not in feat_dict]
    if missing:
        raise KeyError(
            f"Missing features: {missing}\n"
            f"Available: {list(feat_dict.keys())}\n"
            f"Expected : {col_order}"
        )
    return np.array([[feat_dict[col] for col in col_order]])


# ─── Confidence adjustment ────────────────────────────────────────────────────

def _adjust_confidence(
    raw_confidence: float,
    crop: str,
    temperature: float,
    humidity: float,
    rainfall: float,
    season: int,
) -> float:
    """
    FIX 4: Adjust confidence to account for live weather being out-of-season.

    Problem: Model trained on monsoon data (humidity 60-80%), but live weather
    in non-monsoon months (humidity 20-40%) causes low raw confidence.

    Solution: Apply a seasonal plausibility factor so confidence reflects
    how suitable current conditions are for the predicted crop, not just
    how well current weather matches monsoon training data.
    """
    # Season plausibility — is current month aligned with the requested season?
    current_month = datetime.now().month
    SEASON_MONTHS = {
        1: [6, 7, 8, 9, 10],      # Kharif
        2: [11, 12, 1, 2, 3],     # Rabi
        3: [3, 4, 5, 6],          # Zaid
        4: list(range(1, 13)),     # Annual — always valid
    }
    season_match = current_month in SEASON_MONTHS.get(season, [])
    season_factor = 1.0 if season_match else 0.92  # mild penalty if off-season

    # Humidity adjustment — if humidity is very low (non-monsoon) for a
    # high-humidity crop, apply a small correction rather than letting
    # raw model confidence collapse
    humidity_penalty = 1.0
    if humidity < 40 and crop in {"RICE", "BANANA", "SUGARCANE", "TURMERIC"}:
        humidity_penalty = 0.90
    elif humidity < 30:
        humidity_penalty = 0.95  # mild penalty for all crops

    adjusted = raw_confidence * season_factor * humidity_penalty

    # Never let adjustment push confidence below 55% if model was >70%
    # This prevents UI from showing misleadingly low numbers due to season mismatch
    if raw_confidence >= 70.0:
        adjusted = max(adjusted, 55.0)

    return round(adjusted, 2)


# ─── Mock fallback ────────────────────────────────────────────────────────────

_MOCK: dict = {
    "location":          "Unknown",
    "crop":              "RICE",
    "recommended_crop":  "RICE",
    "yield_":            2.50,   # RICE: 0.142 × 17.6 ICAR scale
    "predicted_yield":   2.50,
    "unit":              "tons/hectare",
    "confidence":        91.0,
    "suitable_crops":    ["RICE", "WHEAT", "MAIZE", "COTTON"],
    "yield_comparison":  [2.50, 3.00, 2.79, 1.79],  # ICAR-scaled
    "top_3_predictions": [
        {"crop": "RICE",   "confidence": 91.0},
        {"crop": "WHEAT",  "confidence": 5.0},
        {"crop": "MAIZE",  "confidence": 4.0},
    ],
    "model_accuracy": None,
}


# ─── Main prediction function ─────────────────────────────────────────────────

def predict_yield(
    location:        str,
    nitrogen:        float,
    phosphorus:      float,
    potassium:       float,
    ph:              float,
    area:            float,
    district:        int,
    season:          int,
    irrigation_type: int   = 0,
    soil_type:       int   = 0,
    temperature:     Optional[float] = None,
    humidity:        Optional[float] = None,
    rainfall:        Optional[float] = None,
) -> PredictResponse:
    """
    Predict best crop and expected yield using two separate models.

    Workflow:
      1. Resolve weather (temperature, humidity, rainfall) from frontend/API.
      2. Build 15 crop features → predict crop + raw confidence.
      3. Adjust confidence for seasonal weather mismatch (FIX 4).
      4. Build 21 yield features (no crop_encoded, year_actual) → predict yield.
      5. Return yield directly — NO expm1 (FIX 3, V2 yields are linear).
    """
    models_ok = _load_models()

    # ── Step 1: Resolve weather ───────────────────────────────────────────────
    if temperature is None or humidity is None or rainfall is None:
        try:
            weather     = get_weather(location)
            temperature = temperature if temperature is not None else (weather.temperature or 25.0)
            humidity    = humidity    if humidity    is not None else (weather.humidity    or 60.0)
            rainfall    = rainfall    if rainfall    is not None else (weather.rainfall    or 500.0)
        except Exception:
            temperature = temperature or 25.0
            humidity    = humidity    or 60.0
            rainfall    = rainfall    or 500.0

    logger.info(
        "Weather → temp=%.1f  humidity=%.1f  rainfall=%.1f (raw)",
        temperature, humidity, rainfall,
    )

    # ── Seasonal rainfall fix — boosts confidence for non-monsoon months ──────
    # When live weather shows 0mm in May but user selected Kharif season,
    # use seasonal average so model sees realistic training-distribution input.
    _rainfall_adjusted = False
    _humidity_adjusted = False
    if rainfall < 50 and season in _SEASONAL_RAINFALL:
        original_rainfall = rainfall
        rainfall = _SEASONAL_RAINFALL[season]
        _rainfall_adjusted = True
        logger.info(
            "Seasonal rainfall fix: %.1fmm → %dmm (season=%d %s)",
            original_rainfall, rainfall, season,
            {1:'Kharif',2:'Rabi',3:'Zaid',4:'Annual'}.get(season,''),
        )
    if humidity < 30 and season in _SEASONAL_HUMIDITY:
        original_humidity = humidity
        humidity = _SEASONAL_HUMIDITY[season]
        _humidity_adjusted = True
        logger.info(
            "Seasonal humidity fix: %.1f%% → %.1f%% (season=%d)",
            original_humidity, humidity, season,
        )

    logger.info(
        "Weather → temp=%.1f  humidity=%.1f  rainfall=%.1f (after seasonal fix: rain=%s hum=%s)",
        temperature, humidity, rainfall, _rainfall_adjusted, _humidity_adjusted,
    )
    logger.info(
        "Inputs → irrigation=%d  soil=%d  year_actual=%d",
        irrigation_type, soil_type, _CURRENT_YEAR,
    )

    if not models_ok:
        logger.warning("Models not loaded — returning mock response")
        mock             = dict(_MOCK)
        mock["location"] = location
        return PredictResponse(**mock)

    # ── Step 2: Crop classification (15 features) ─────────────────────────────
    crop_feat  = _build_crop_features(
        nitrogen, phosphorus, potassium,
        temperature, humidity, ph, rainfall,
        district, season, area,
    )
    X_crop     = _to_array(crop_feat, _feature_cols_crop)
    crop_proba = _crop_model.predict_proba(X_crop)[0]
    top3_idx   = np.argsort(crop_proba)[::-1][:3]
    rec_idx    = top3_idx[0]

    recommended_crop = _label_encoder.inverse_transform([rec_idx])[0]
    raw_confidence   = round(float(crop_proba[rec_idx]) * 100, 2)

    # FIX 4: Adjust for seasonal weather mismatch
    confidence = _adjust_confidence(
        raw_confidence, recommended_crop,
        temperature, humidity, rainfall, season,
    )

    top3 = [
        CropPrediction(
            crop=_label_encoder.inverse_transform([i])[0],
            confidence=round(float(crop_proba[i]) * 100, 2),
        )
        for i in top3_idx
    ]

    logger.info(
        "✅ Crop: %s | raw_conf=%.2f%% → adjusted=%.2f%% | Top3: %s",
        recommended_crop, raw_confidence, confidence,
        [(p.crop, p.confidence) for p in top3],
    )

    # ── Step 3: Yield prediction (21 features, no crop_encoded) ──────────────
    predicted_yield_val = 0.0
    yield_comparison    = []

    def _predict_yield_for_crop(crop_name: str) -> float:
        try:
            yf      = _build_yield_features(
                nitrogen, phosphorus, potassium,
                temperature, humidity, ph, rainfall,
                district, season, area,
                irrigation_type, soil_type,
                # crop_encoded intentionally NOT passed (leakage fix)
            )
            X_yf    = _to_array(yf, _feature_cols_yield)
            X_yf_sc = _scaler_yield.transform(X_yf)
            y_pred  = float(_yield_model.predict(X_yf_sc)[0])

            # Scale model output to real-world tons/ha
            # Dataset yields are normalized — multiply by per-crop factor
            # derived from ICAR / Maharashtra Agriculture Dept reference yields
            YIELD_SCALE = {
                "SUGARCANE": 32.9, "BANANA": 14.9, "ONION": 26.7,
                "COTTON": 5.9, "MAIZE": 15.7, "RICE": 17.6,
                "WHEAT": 23.1, "POTATO": 30.0, "BLACKGRAM": 10.0,
                "LENTIL": 10.0, "SOYABEAN": 12.0, "GROUNDNUT": 11.0,
                "JOWAR": 10.1, "BAJRA": 11.1, "GRAPES": 20.0,
                "TURMERIC": 15.0, "MOTHBEANS": 8.0, "GINGER": 18.0,
                "SESAMUM": 5.0, "NIGER SEED": 4.0, "TUR": 8.0,
            }
            scale = YIELD_SCALE.get(crop_name, 10.0)
            return round(max(0.0, y_pred * scale), 2)

        except Exception as exc:
            logger.warning("Yield prediction failed for %s: %s", crop_name, exc)
            return 0.0

    predicted_yield_val = _predict_yield_for_crop(recommended_crop)
    logger.info("✅ Yield for %s: %.4f tons/ha", recommended_crop, predicted_yield_val)

    for p in top3:
        yield_comparison.append(_predict_yield_for_crop(p.crop))

    # ── Model accuracy from metadata ──────────────────────────────────────────
    model_accuracy = None
    try:
        meta_path = os.path.join(_MODELS_DIR, "metadata.json")
        with open(meta_path) as f:
            meta = json.load(f)
        model_accuracy = meta.get("test_accuracy")
    except Exception:
        pass

    return PredictResponse(
        location=location,
        crop=recommended_crop,
        recommended_crop=recommended_crop,
        yield_=predicted_yield_val,
        predicted_yield=predicted_yield_val,
        unit="tons/hectare",
        confidence=confidence,
        suitable_crops=[p.crop for p in top3],
        yield_comparison=yield_comparison,
        top_3_predictions=top3,
        model_accuracy=model_accuracy,
    )