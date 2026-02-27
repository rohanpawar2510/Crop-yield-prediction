"""
recommendation_service.py — Smart farming recommendations.

Phase 5 will replace the mock below with Gemini AI responses using
config.GEMINI_API_KEY.
"""

from __future__ import annotations

from models.schemas import FertilizerDetail, RecommendResponse


# Mock response — matches MOCK_RECOMMENDATIONS in frontend/js/api.js
_MOCK_FERTILIZER = FertilizerDetail(
    primary="NPK 20-10-10",
    amount="150 kg/hectare",
    schedule="Apply at sowing and 30 days after germination",
    alternatives=["Urea + DAP", "Organic compost (5 ton/ha)"],
    distribution={"Nitrogen": 40, "Phosphorus": 25, "Potassium": 20, "Organic": 15},
)

_MOCK_RESPONSE = RecommendResponse(
    fertilizer=_MOCK_FERTILIZER,
    crop_rotation=(
        "Follow Rice with Legumes (Lentil/Chickpea) next season "
        "to restore soil nitrogen."
    ),
    irrigation="Maintain soil moisture at 60–70%. Irrigate every 5–7 days during dry spells.",
    pest_management=(
        "Monitor for stem borers. Use integrated pest management "
        "— neem-based sprays preferred."
    ),
    general=(
        "Soil pH is slightly acidic. Consider liming (250 kg/ha of agricultural lime) "
        "to raise pH towards 6.5."
    ),
)


def get_recommendations(
    location: str,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph: float,
) -> RecommendResponse:
    """Return smart farming recommendations for the given inputs.

    Args:
        location: City or region name.
        nitrogen: Nitrogen content in kg/ha.
        phosphorus: Phosphorus content in kg/ha.
        potassium: Potassium content in kg/ha.
        ph: Soil pH value (0–14).

    Returns:
        RecommendResponse with mock data until Gemini AI is integrated in
        Phase 5.
    """
    # TODO (Phase 5): call Gemini API with config.GEMINI_API_KEY.
    return _MOCK_RESPONSE
