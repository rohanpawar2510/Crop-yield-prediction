"""
prediction_service.py — Crop yield prediction logic.

Phase 2 will replace the mock below with a real scikit-learn / TensorFlow
model loaded from config.MODEL_PATH.
"""

from __future__ import annotations

from models.schemas import PredictResponse


# Mock response — matches the constants in frontend/js/api.js
_MOCK: dict = {
    "crop": "Rice",
    "yield": 4.2,
    "unit": "tons/hectare",
    "confidence": 91,
    "suitable_crops": ["Rice", "Wheat", "Maize", "Soybean"],
    "yield_comparison": [4.2, 3.8, 5.1, 2.9],
}


def predict_yield(
    location: str,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph: float,
) -> PredictResponse:
    """Return a crop yield prediction for the given soil parameters.

    Args:
        location: City or region name.
        nitrogen: Nitrogen content in kg/ha.
        phosphorus: Phosphorus content in kg/ha.
        potassium: Potassium content in kg/ha.
        ph: Soil pH value (0–14).

    Returns:
        PredictResponse with mock data until the ML model is integrated.
    """
    # TODO (Phase 2): load model from config.MODEL_PATH and run inference.
    return PredictResponse(**_MOCK)
