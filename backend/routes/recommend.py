"""
recommend.py — POST /api/recommend

Accepts soil / location parameters and returns smart farming recommendations.
"""

from fastapi import APIRouter
from models.schemas import SoilInput, RecommendResponse
from services.recommendation_service import get_recommendations

router = APIRouter()


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    summary="Get smart farming recommendations",
)
def recommend(data: SoilInput) -> RecommendResponse:
    """Generate fertilizer, irrigation, and crop-rotation recommendations.

    **Request body** (JSON):
    - `location` — city or region name
    - `nitrogen` — N content in kg/ha (0–140)
    - `phosphorus` — P content in kg/ha (0–145)
    - `potassium` — K content in kg/ha (0–205)
    - `ph` — soil pH (0–14)

    **Response** fields match the frontend `MOCK_RECOMMENDATIONS` constant.
    Phase 5 will integrate Gemini AI for personalised advice.
    """
    return get_recommendations(
        location=data.location,
        nitrogen=data.nitrogen,
        phosphorus=data.phosphorus,
        potassium=data.potassium,
        ph=data.ph,
    )
