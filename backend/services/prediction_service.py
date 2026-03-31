"""
prediction_service.py — Crop recommendation and yield prediction logic.

Loads models from backend/models/:
  crop_model.pkl       — sklearn Pipeline (StandardScaler + RandomForest)
  yield_model.pkl      — RandomForestRegressor
  label_encoder.pkl    — LabelEncoder for crop names
  scaler_yield.pkl     — StandardScaler for yield features
  feature_cols.pkl     — {'crop': [...], 'yield': [...]} feature column lists

Input features (14 crop / 15 yield):
  User:        nitrogen, phosphorus, potassium, ph, area, district, season
  Weather API: temperature, humidity, rainfall
  Engineered:  NPK_total, NPK_ratio, Climate_score, Temp_humidity_interaction, Soil_quality_score
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

import numpy as np
import joblib

from models.schemas import CropPrediction, PredictResponse
from services.weather_service import get_weather

logger = logging.getLogger(__name__)

# ─── Model registry ───────────────────────────────────────────────────────────

_MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")

_crop_model    = None
_yield_model   = None
_label_encoder = None
_scaler_yield  = None
_feature_cols  = None
_models_loaded = False


def _load_models() -> bool:
    """Load all model artefacts from models/. Runs once. Returns True on success."""
    global _crop_model, _yield_model, _label_encoder
    global _scaler_yield, _feature_cols, _models_loaded

    if _models_loaded:
        return _crop_model is not None

    try:
        _crop_model    = joblib.load(os.path.join(_MODELS_DIR, "crop_model.pkl"))
        _yield_model   = joblib.load(os.path.join(_MODELS_DIR, "yield_model.pkl"))
        _label_encoder = joblib.load(os.path.join(_MODELS_DIR, "label_encoder.pkl"))
        _scaler_yield  = joblib.load(os.path.join(_MODELS_DIR, "scaler_yield.pkl"))
        _feature_cols  = joblib.load(os.path.join(_MODELS_DIR, "feature_cols.pkl"))

        logger.info("✅ All models loaded successfully")
        logger.info("   Crops      : %s", list(_label_encoder.classes_))
        logger.info("   Crop feats : %s", _feature_cols["crop"])
        logger.info("   Yield feats: %s", _feature_cols["yield"])

    except Exception as exc:
        logger.error("❌ Model loading failed: %s", exc)
        _crop_model = None

    _models_loaded = True
    return _crop_model is not None


# ─── Feature engineering ──────────────────────────────────────────────────────
# NOTE: Must match train_models.py EXACTLY — same features, same names, same order.
# Current models were trained WITH humidity (estimated in training).
# After retraining without humidity, remove humidity from here too.

def _build_features(
    nitrogen:    float,
    phosphorus:  float,
    potassium:   float,
    temperature: float,
    humidity:    float,    # ← from Weather API (real value at inference)
    ph:          float,
    rainfall:    float,
    district:    int,
    season:      int,
    area:        float,
) -> dict:
    """Build base + engineered features. Must match train_models.py exactly."""
    NPK_total                 = nitrogen + phosphorus + potassium
    NPK_ratio                 = nitrogen / (phosphorus + potassium + 1e-6)
    Climate_score             = 0.5 * temperature + 0.5 * (rainfall / 100.0)
    Temp_humidity_interaction = temperature * humidity
    Soil_quality_score        = 10.0 * np.exp(-0.5 * ((ph - 6.5) / 0.8) ** 2)

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
        "NPK_total":                  NPK_total,
        "NPK_ratio":                  NPK_ratio,
        "Climate_score":              Climate_score,
        "Temp_humidity_interaction":  Temp_humidity_interaction,
        "Soil_quality_score":         Soil_quality_score,
    }


def _features_to_array(feat_dict: dict, col_order: list) -> np.ndarray:
    """Convert feature dict to numpy array in the exact column order the model expects."""
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
    "unit":              "kg/hectare",
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
    location:    str,
    nitrogen:    float,
    phosphorus:  float,
    potassium:   float,
    ph:          float,
    area:        float,
    district:    int,
    season:      int,
    temperature: Optional[float] = None,
    humidity:    Optional[float] = None,
    rainfall:    Optional[float] = None,
) -> PredictResponse:
    """
    Predict the best crop and expected yield.

    Workflow:
      1. Use temperature/humidity/rainfall from frontend (Weather API).
         Only fetch from weather service if values not provided.
      2. Build features (base + engineered) for crop classification.
      3. Predict crop using crop_model pipeline (includes StandardScaler).
      4. Build yield features (crop features + crop_encoded).
      5. Predict yield using yield_model + scaler_yield.
      6. Reverse log-transform: actual_yield = expm1(log_yield).
      7. Return crop, confidence, top-3, yield, model accuracy.
    """
    models_ok = _load_models()

    # ── Step 1: Resolve weather values ───────────────────────────────────────
    if temperature is None or rainfall is None:
        try:
            weather     = get_weather(location)
            temperature = temperature or weather.temperature or 25.0
            humidity    = humidity    or weather.humidity    or 70.0
            rainfall    = rainfall    or weather.rainfall    or 500.0
        except Exception:
            temperature = temperature or 25.0
            humidity    = humidity    or 70.0
            rainfall    = rainfall    or 500.0
    else:
        # Frontend already sent weather values — use directly
        humidity = humidity if humidity is not None else 70.0

    logger.info(
        "Weather → temp=%.1f  humidity=%.1f  rainfall=%.1f",
        temperature, humidity, rainfall,
    )

    # ── Fall back to mock if models not loaded ────────────────────────────────
    if not models_ok:
        logger.warning("Models not loaded — returning mock response")
        mock             = dict(_MOCK)
        mock["location"] = location
        return PredictResponse(**mock)

    # ── Step 2: Build feature dict ────────────────────────────────────────────
    feat_dict = _build_features(
        nitrogen, phosphorus, potassium,
        temperature, humidity, ph, rainfall,
        district, season, area,
    )

    # ── Step 3: Crop classification ───────────────────────────────────────────
    crop_cols = _feature_cols["crop"]
    X_crop    = _features_to_array(feat_dict, crop_cols)

    logger.debug("Crop input → %s", dict(zip(crop_cols, X_crop[0])))

    crop_proba      = _crop_model.predict_proba(X_crop)[0]
    top3_idx        = np.argsort(crop_proba)[::-1][:3]
    recommended_idx = top3_idx[0]

    recommended_crop = _label_encoder.inverse_transform([recommended_idx])[0]
    confidence       = round(float(crop_proba[recommended_idx]) * 100, 2)

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

    # ── Step 4: Build yield features ──────────────────────────────────────────
    crop_encoded = int(recommended_idx)
    yield_cols   = _feature_cols["yield"]
    feat_dict_y  = {**feat_dict, "crop_encoded": crop_encoded}
    X_yield      = _features_to_array(feat_dict_y, yield_cols)

    # ── Step 5 & 6: Yield prediction + reverse log-transform ─────────────────
    predicted_yield_val = 0.0
    try:
        X_yield_sc          = _scaler_yield.transform(X_yield)
        log_yield           = float(_yield_model.predict(X_yield_sc)[0])
        predicted_yield_val = round(float(np.expm1(log_yield)), 2)
        logger.info("✅ Yield: log=%.4f → actual=%.2f kg/ha", log_yield, predicted_yield_val)
    except Exception as exc:
        logger.warning("Yield prediction failed: %s", exc)

    # ── Yield comparison for top-3 crops ──────────────────────────────────────
    yield_comparison = []
    for p in top3:
        try:
            c_idx   = int(_label_encoder.transform([p.crop])[0])
            yf_dict = {**feat_dict, "crop_encoded": c_idx}
            X_yf    = _features_to_array(yf_dict, yield_cols)
            X_yf_sc = _scaler_yield.transform(X_yf)
            log_y   = float(_yield_model.predict(X_yf_sc)[0])
            yield_comparison.append(round(float(np.expm1(log_y)), 2))
        except Exception as exc:
            logger.warning("Yield comparison failed for %s: %s", p.crop, exc)
            yield_comparison.append(0.0)

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
        unit="kg/hectare",
        confidence=confidence,
        suitable_crops=[p.crop for p in top3],
        yield_comparison=yield_comparison,
        top_3_predictions=top3,
        model_accuracy=model_accuracy,
    )