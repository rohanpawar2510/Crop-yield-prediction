"""
prediction_service.py — Crop recommendation and yield prediction logic.

Loads trained Random Forest models (crop recommendation classifier and
yield prediction regressor) and runs inference.  Falls back to mock data
when model files are not available.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import numpy as np
import joblib

import config
from models.schemas import PredictResponse
from services.weather_service import get_weather

logger = logging.getLogger(__name__)

# ─── Model loading ────────────────────────────────────────────────────────────

_crop_model = None
_yield_model = None
_label_encoder = None
_models_loaded: bool = False


def _load_models() -> None:
    """Attempt to load ML models from disk. Runs once at first prediction."""
    global _crop_model, _yield_model, _label_encoder, _models_loaded
    if _models_loaded:
        return

    base = os.path.dirname(__file__)
    crop_path = os.path.join(base, "..", config.CROP_MODEL_PATH)
    yield_path = os.path.join(base, "..", config.YIELD_MODEL_PATH)
    encoder_path = os.path.join(base, "..", config.LABEL_ENCODER_PATH)

    try:
        _crop_model = joblib.load(crop_path)
        _yield_model = joblib.load(yield_path)
        _label_encoder = joblib.load(encoder_path)
        logger.info("ML models loaded successfully from %s, %s, %s", crop_path, yield_path, encoder_path)
    except FileNotFoundError as exc:
        logger.warning("Model file not found (%s) — falling back to mock predictions", exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Error loading models (%s) — falling back to mock predictions", exc)

    _models_loaded = True


# ─── Mock fallback ────────────────────────────────────────────────────────────

_MOCK: dict = {
    "crop": "Rice",
    "recommended_crop": "Rice",
    "yield": 4.2,
    "predicted_yield": 4.2,
    "unit": "tons/hectare",
    "confidence": 91,
    "suitable_crops": ["Rice", "Wheat", "Maize", "Soybean"],
    "yield_comparison": [4.2, 3.8, 5.1, 2.9],
}


# ─── Defaults for climate values ──────────────────────────────────────────────

_DEFAULT_TEMP = 25.0
_DEFAULT_HUMIDITY = 70.0
_DEFAULT_RAINFALL = 150.0


def _fetch_climate(location: str) -> tuple[float, float, float]:
    """Fetch temperature, humidity, and rainfall from the weather service.

    Returns defaults if the weather API is unavailable.
    """
    try:
        weather = get_weather(location)
        return (
            weather.temperature if weather.temperature else _DEFAULT_TEMP,
            weather.humidity if weather.humidity else _DEFAULT_HUMIDITY,
            weather.rainfall if weather.rainfall else _DEFAULT_RAINFALL,
        )
    except Exception:  # noqa: BLE001
        logger.info("Could not fetch weather for %r — using defaults", location)
        return _DEFAULT_TEMP, _DEFAULT_HUMIDITY, _DEFAULT_RAINFALL


def predict_yield(
    location: str,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph: float,
    temperature: Optional[float] = None,
    humidity: Optional[float] = None,
    rainfall: Optional[float] = None,
) -> PredictResponse:
    """Predict the best crop **and** expected yield for the given parameters.

    Workflow:
      1. If temperature/humidity/rainfall are not supplied, fetch them from
         the OpenWeather API using *location*.
      2. Run the crop recommendation model to predict the best crop.
      3. Pass soil + climate + predicted crop into the yield regression model.
      4. Return both the recommended crop and the predicted yield.

    Falls back to mock data when models are not loaded.
    """
    _load_models()

    # ── Resolve climate values ───────────────────────────────────────────
    if temperature is None or humidity is None or rainfall is None:
        w_temp, w_hum, w_rain = _fetch_climate(location)
        temperature = temperature if temperature is not None else w_temp
        humidity = humidity if humidity is not None else w_hum
        rainfall = rainfall if rainfall is not None else w_rain

    # ── Fall back to mock if models not available ────────────────────────
    if _crop_model is None or _yield_model is None or _label_encoder is None:
        return PredictResponse(**_MOCK)

    # ── Step 1: Crop recommendation ──────────────────────────────────────
    crop_features = np.array([[nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall]])
    crop_encoded = _crop_model.predict(crop_features)[0]
    recommended_crop: str = _label_encoder.inverse_transform([crop_encoded])[0]

    # Confidence from class probabilities
    proba = _crop_model.predict_proba(crop_features)[0]
    confidence = int(round(max(proba) * 100))

    # ── Step 2: Yield prediction ─────────────────────────────────────────
    yield_features = np.array([[nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall, crop_encoded]])
    predicted_yield_val: float = round(float(_yield_model.predict(yield_features)[0]), 2)

    # ── Step 3: Suitable crops + yield comparison ────────────────────────
    top_n = min(4, len(_label_encoder.classes_))
    top_indices = np.argsort(proba)[::-1][:top_n]
    suitable_crops = [_label_encoder.inverse_transform([i])[0] for i in top_indices]
    yield_comparison: list[float] = []
    for idx in top_indices:
        yf = np.array([[nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall, idx]])
        yield_comparison.append(round(float(_yield_model.predict(yf)[0]), 2))

    return PredictResponse(
        crop=recommended_crop,
        recommended_crop=recommended_crop,
        yield_=predicted_yield_val,
        predicted_yield=predicted_yield_val,
        unit="tons/hectare",
        confidence=confidence,
        suitable_crops=suitable_crops,
        yield_comparison=yield_comparison,
    )
