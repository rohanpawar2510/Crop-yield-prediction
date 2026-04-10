"""
prediction_service.py — Crop recommendation and yield prediction logic.

TWO SEPARATE MODELS:
  1. Crop Model (crop_model.pkl) — 15 features
     Trained on Final_Agriculture_Dataset_V2.csv

  2. Yield Model (yield_model.pkl) — 21 features
     Trained on Yield_Dataset_V1.csv
     Includes: irrigation_type, soil_type, year (new features)

Model files in backend/models/:
  crop_model.pkl          — Pipeline (StandardScaler + RandomForest)
  label_encoder.pkl       — LabelEncoder for crop model
  feature_cols.pkl        — crop feature column list
  yield_model.pkl         — RandomForestRegressor
  scaler_yield.pkl        — StandardScaler for yield
  label_encoder_yield.pkl — LabelEncoder for yield model
  feature_cols_yield.pkl  — yield feature column list
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

# Crop model
_crop_model          = None
_label_encoder       = None
_feature_cols_crop   = None

# Yield model (separate — richer features)
_yield_model         = None
_scaler_yield        = None
_label_encoder_yield = None
_feature_cols_yield  = None

_models_loaded = False

# Current year normalized (2010 = base year used in training)
_BASE_YEAR = 2010
_CURRENT_YEAR_NORM = datetime.now().year - _BASE_YEAR  # e.g. 2024-2010 = 14


def _load_models() -> bool:
    """Load all model artefacts. Runs once. Returns True on success."""
    global _crop_model, _label_encoder, _feature_cols_crop
    global _yield_model, _scaler_yield, _label_encoder_yield
    global _feature_cols_yield, _models_loaded

    if _models_loaded:
        return _crop_model is not None

    try:
        # ── Crop model ────────────────────────────────────────────────────────
        _crop_model        = joblib.load(os.path.join(_MODELS_DIR, "crop_model.pkl"))
        _label_encoder     = joblib.load(os.path.join(_MODELS_DIR, "label_encoder.pkl"))
        _feat_cols_raw     = joblib.load(os.path.join(_MODELS_DIR, "feature_cols.pkl"))
        _feature_cols_crop = (
            _feat_cols_raw["crop"]
            if isinstance(_feat_cols_raw, dict)
            else _feat_cols_raw
        )

        # ── Yield model ───────────────────────────────────────────────────────
        _yield_model         = joblib.load(os.path.join(_MODELS_DIR, "yield_model.pkl"))
        _scaler_yield        = joblib.load(os.path.join(_MODELS_DIR, "scaler_yield.pkl"))
        _label_encoder_yield = joblib.load(os.path.join(_MODELS_DIR, "label_encoder_yield.pkl"))
        _feature_cols_yield  = joblib.load(os.path.join(_MODELS_DIR, "feature_cols_yield.pkl"))

        logger.info("✅ All models loaded successfully")
        logger.info("   Crop classes  : %s", list(_label_encoder.classes_))
        logger.info("   Crop features : %s", _feature_cols_crop)
        logger.info("   Yield features: %s", _feature_cols_yield)
        logger.info("   Year norm     : %d (year %d)", _CURRENT_YEAR_NORM,
                    _CURRENT_YEAR_NORM + _BASE_YEAR)

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
        "nitrogen":                   nitrogen,
        "phosphorus":                 phosphorus,
        "potassium":                  potassium,
        "temperature":                temperature,
        "humidity":                   humidity,
        "ph":                         ph,
        "rainfall":                   rainfall,
        "district":                   district,
        "season":                     season,
        "area":                       area,
        "NPK_total":                  nitrogen + phosphorus + potassium,
        "NPK_ratio":                  nitrogen / (phosphorus + potassium + 1e-6),
        "Climate_score":              0.5 * temperature + 0.5 * (rainfall / 100.0),
        "Temp_humidity_interaction":  temperature * humidity,
        "Soil_quality_score":         10.0 * np.exp(-0.5 * ((ph - 6.5) / 0.8) ** 2),
    }


def _build_yield_features(
    nitrogen: float, phosphorus: float, potassium: float,
    temperature: float, humidity: float,
    ph: float, rainfall: float,
    district: int, season: int, area: float,
    irrigation_type: int,
    soil_type: int,
    crop_encoded: int,
) -> dict:
    """21 features for yield model. Matches train_yield_model.py."""
    NPK_total = nitrogen + phosphorus + potassium
    return {
        "nitrogen":                   nitrogen,
        "phosphorus":                 phosphorus,
        "potassium":                  potassium,
        "temperature":                temperature,
        "humidity":                   humidity,
        "ph":                         ph,
        "rainfall":                   rainfall,
        "district":                   district,
        "season":                     season,
        "area":                       area,
        "irrigation_type":            irrigation_type,
        "soil_type":                  soil_type,
        "year":                       _CURRENT_YEAR_NORM,
        "NPK_total":                  NPK_total,
        "NPK_ratio":                  nitrogen / (phosphorus + potassium + 1e-6),
        "Climate_score":              0.5 * temperature + 0.5 * (rainfall / 100.0),
        "Temp_humidity_interaction":  temperature * humidity,
        "Soil_quality_score":         10.0 * np.exp(-0.5 * ((ph - 6.5) / 0.8) ** 2),
        "rain_per_temp":              rainfall / (temperature + 1e-6),
        "N_to_P_ratio":               nitrogen / (phosphorus + 1e-6),
        "crop_encoded":               crop_encoded,
    }


def _to_array(feat_dict: dict, col_order: list) -> np.ndarray:
    """Convert feature dict → numpy array in exact column order."""
    missing = [c for c in col_order if c not in feat_dict]
    if missing:
        raise KeyError(
            f"Missing features: {missing}\n"
            f"Available: {list(feat_dict.keys())}\n"
            f"Expected : {col_order}"
        )
    return np.array([[feat_dict[col] for col in col_order]])


# ─── Mock fallback ────────────────────────────────────────────────────────────

_MOCK: dict = {
    "location":          "Unknown",
    "crop":              "RICE",
    "recommended_crop":  "RICE",
    "yield_":            47.3,
    "predicted_yield":   47.3,
    "unit":              "tons/hectare",
    "confidence":        91.0,
    "suitable_crops":    ["RICE", "WHEAT", "MAIZE", "COTTON"],
    "yield_comparison":  [47.3, 220.0, 66.6, 266.7],
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
    irrigation_type: int   = 0,   # 0=Rainfed (default)
    soil_type:       int   = 0,   # 0=Black (default)
    temperature:     Optional[float] = None,
    humidity:        Optional[float] = None,
    rainfall:        Optional[float] = None,
) -> PredictResponse:
    """
    Predict best crop and expected yield using two separate models.

    Workflow:
      1. Resolve weather (temperature, humidity, rainfall) from frontend/API.
      2. Build 15 crop features → predict crop + confidence.
      3. Build 21 yield features (includes irrigation, soil, year) → predict yield.
      4. Reverse log-transform yield: actual = expm1(log_yield).
      5. Return crop, confidence, top-3, yield comparison, model accuracy.
    """
    models_ok = _load_models()

    # ── Step 1: Resolve weather values ───────────────────────────────────────
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
        "Weather → temp=%.1f  humidity=%.1f  rainfall=%.1f",
        temperature, humidity, rainfall,
    )
    logger.info(
        "User inputs → irrigation=%d  soil=%d  year_norm=%d",
        irrigation_type, soil_type, _CURRENT_YEAR_NORM,
    )

    # ── Fall back to mock if models not loaded ────────────────────────────────
    if not models_ok:
        logger.warning("Models not loaded — returning mock response")
        mock             = dict(_MOCK)
        mock["location"] = location
        return PredictResponse(**mock)

    # ── Step 2: Crop classification (15 features) ─────────────────────────────
    crop_feat = _build_crop_features(
        nitrogen, phosphorus, potassium,
        temperature, humidity, ph, rainfall,
        district, season, area,
    )
    X_crop      = _to_array(crop_feat, _feature_cols_crop)
    crop_proba  = _crop_model.predict_proba(X_crop)[0]
    top3_idx    = np.argsort(crop_proba)[::-1][:3]
    rec_idx     = top3_idx[0]

    recommended_crop = _label_encoder.inverse_transform([rec_idx])[0]
    confidence       = round(float(crop_proba[rec_idx]) * 100, 2)

    top3 = [
        CropPrediction(
            crop=_label_encoder.inverse_transform([i])[0],
            confidence=round(float(crop_proba[i]) * 100, 2),
        )
        for i in top3_idx
    ]

    logger.info(
        "✅ Crop: %s (%.2f%%) | Top3: %s",
        recommended_crop, confidence,
        [(p.crop, p.confidence) for p in top3],
    )

    # ── Step 3 & 4: Yield prediction (21 features) ────────────────────────────
    predicted_yield_val = 0.0
    yield_comparison    = []

    def _predict_yield_for_crop(crop_name: str) -> float:
        """Predict yield for a given crop name using the yield model."""
        try:
            # Encode crop using yield model's label encoder
            if crop_name not in _label_encoder_yield.classes_:
                logger.warning("Crop %s not in yield model — returning 0", crop_name)
                return 0.0
            c_enc    = int(_label_encoder_yield.transform([crop_name])[0])
            yf       = _build_yield_features(
                nitrogen, phosphorus, potassium,
                temperature, humidity, ph, rainfall,
                district, season, area,
                irrigation_type, soil_type, c_enc,
            )
            X_yf     = _to_array(yf, _feature_cols_yield)
            X_yf_sc  = _scaler_yield.transform(X_yf)
            log_y    = float(_yield_model.predict(X_yf_sc)[0])
            return round(float(np.expm1(log_y)), 2)
        except Exception as exc:
            logger.warning("Yield prediction failed for %s: %s", crop_name, exc)
            return 0.0

    # Predict yield for recommended crop
    predicted_yield_val = _predict_yield_for_crop(recommended_crop)
    logger.info("✅ Yield for %s: %.2f tons/ha", recommended_crop, predicted_yield_val)

    # Yield comparison for top-3 crops
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