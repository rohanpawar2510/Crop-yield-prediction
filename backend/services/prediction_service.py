"""
prediction_service.py — Crop recommendation and yield prediction logic.

Loads the trained CropPredictor from ml_models/ for crop classification
and the yield regression model from models/ for yield estimation.
Falls back to mock data when model files are not available.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

import numpy as np
import joblib

import config
from models.schemas import CropPrediction, PredictResponse
from services.weather_service import get_weather

logger = logging.getLogger(__name__)

# ─── CropPredictor (ml_models) ────────────────────────────────────────────────

_crop_predictor = None
_crop_predictor_loaded: bool = False


def _load_crop_predictor():
    """Attempt to load the CropPredictor from ml_models/. Runs once."""
    global _crop_predictor, _crop_predictor_loaded
    if _crop_predictor_loaded:
        return _crop_predictor

    try:
        from ml_models.predict_with_model import CropPredictor
        predictor = CropPredictor()
        predictor._load()  # trigger model load to detect errors early
        _crop_predictor = predictor
        logger.info("CropPredictor loaded successfully from ml_models/")
    except Exception as exc:  # noqa: BLE001
        logger.warning("CropPredictor not available (%s) — will try legacy models", exc)
        _crop_predictor = None

    _crop_predictor_loaded = True
    return _crop_predictor


# ─── Simple yield model (8-feature) ──────────────────────────────────────────

_yield_model = None
_legacy_label_encoder = None
_scaler_yield = None
_legacy_models_loaded: bool = False

_MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


def _load_legacy_models() -> None:
    """Attempt to load the simple 8-feature yield model from models/. Runs once."""
    global _yield_model, _legacy_label_encoder, _scaler_yield, _legacy_models_loaded
    if _legacy_models_loaded:
        return

    yield_path = os.path.join(_MODELS_DIR, "yield_model_simple.pkl")
    encoder_path = os.path.join(_MODELS_DIR, "label_encoder_simple.pkl")
    scaler_path = os.path.join(_MODELS_DIR, "scaler_yield_simple.pkl")

    try:
        _yield_model = joblib.load(yield_path)
        _legacy_label_encoder = joblib.load(encoder_path)
        _scaler_yield = joblib.load(scaler_path)
        logger.info("Simple yield model loaded from %s", yield_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Yield model not available (%s)", exc)

    _legacy_models_loaded = True


# ─── Mock fallback ────────────────────────────────────────────────────────────

_MOCK: dict = {
    "location": "Unknown",
    "crop": "Rice",
    "recommended_crop": "Rice",
    "yield": 4.2,
    "predicted_yield": 4.2,
    "unit": "tons/hectare",
    "confidence": 91.0,
    "suitable_crops": ["Rice", "Wheat", "Maize", "Soybean"],
    "yield_comparison": [4.2, 3.8, 5.1, 2.9],
    "top_3_predictions": [
        {"crop": "Rice", "confidence": 91.0},
        {"crop": "Wheat", "confidence": 5.0},
        {"crop": "Maize", "confidence": 4.0},
    ],
    "model_accuracy": None,
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
    """Predict the best crop and expected yield for the given parameters.

    Workflow:
      1. If temperature/humidity/rainfall are not supplied, fetch them from
         the OpenWeather API using *location*.
      2. Use the CropPredictor (ml_models/) for crop classification with
         top-3 predictions and confidence scores.
      3. Pass soil + climate + predicted crop into the yield regression model.
      4. Return crop, confidence, top-3 predictions, yield, and model accuracy.

    Falls back to mock data when models are not loaded.
    """
    predictor = _load_crop_predictor()
    _load_legacy_models()

    # ── Resolve climate values ───────────────────────────────────────────
    if temperature is None or humidity is None or rainfall is None:
        w_temp, w_hum, w_rain = _fetch_climate(location)
        temperature = temperature if temperature is not None else w_temp
        humidity = humidity if humidity is not None else w_hum
        rainfall = rainfall if rainfall is not None else w_rain

    # ── Fall back to mock if no models available ─────────────────────────
    if predictor is None:
        mock = dict(_MOCK)
        mock["location"] = location
        return PredictResponse(**mock)

    # ── Step 1: Crop classification (CropPredictor) ──────────────────────
    result = predictor.predict(
        N=nitrogen,
        P=phosphorus,
        K=potassium,
        temperature=temperature,
        humidity=humidity,
        ph=ph,
        rainfall=rainfall,
        top_n=3,
    )

    recommended_crop = result["crop"]
    confidence = result["confidence"]
    top3 = [CropPrediction(**p) for p in result["top_predictions"]]
    model_accuracy = result["model_accuracy"] or None

    # ── Step 2: Yield prediction (legacy model, optional) ────────────────
    predicted_yield_val: float = 0.0
    suitable_crops: list[str] = [p.crop for p in top3]
    yield_comparison: list[float] = []

    if _yield_model is not None and _legacy_label_encoder is not None:
        # Encode the crop name using the simple label encoder
        crop_lower = recommended_crop.lower()
        if crop_lower in _legacy_label_encoder.classes_:
            crop_encoded = _legacy_label_encoder.transform([crop_lower])[0]
        else:
            crop_encoded = 0

        # Create yield features with exactly 8 features in correct order
        yield_features = np.array([[nitrogen, phosphorus, potassium,
                                    temperature, humidity, ph, rainfall,
                                    crop_encoded]])
        try:
            predicted_yield_val = round(float(_yield_model.predict(yield_features)[0]), 2)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Yield prediction failed: %s", exc)
            predicted_yield_val = 0.0

        # Yield for top crops
        for p in top3:
            c_lower = p.crop.lower()
            if c_lower in _legacy_label_encoder.classes_:
                idx = _legacy_label_encoder.transform([c_lower])[0]
            else:
                idx = 0

            # Create yield features for comparison with exactly 8 features
            yf = np.array([[nitrogen, phosphorus, potassium,
                            temperature, humidity, ph, rainfall, idx]])
            try:
                yield_comparison.append(round(float(_yield_model.predict(yf)[0]), 2))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Yield comparison prediction failed: %s", exc)
                yield_comparison.append(0.0)

    if not yield_comparison:
        yield_comparison = [0.0] * len(top3)

    return PredictResponse(
        location=location,
        crop=recommended_crop,
        recommended_crop=recommended_crop,
        yield_=predicted_yield_val,
        predicted_yield=predicted_yield_val,
        unit="tons/hectare",
        confidence=confidence,
        suitable_crops=suitable_crops,
        yield_comparison=yield_comparison,
        top_3_predictions=top3,
        model_accuracy=model_accuracy,
    )
