"""
recommend.py — POST /api/recommend

Accepts soil / location parameters and returns smart farming recommendations.
"""

from fastapi import APIRouter
from models.schemas import SoilInputRecommend, RecommendResponse
from services.recommendation_service import get_recommendations

router = APIRouter()


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    summary="Get smart farming recommendations",
)
def recommend(data: SoilInputRecommend) -> RecommendResponse:
    """Generate fertilizer, irrigation, and crop-rotation recommendations.

    **Request body** (JSON):
    - `location` — city or region name
    - `nitrogen` — N content in kg/ha (20–150)
    - `phosphorus` — P content in kg/ha (10–90)
    - `potassium` — K content in kg/ha (5–150)
    - `ph` — soil pH (5.5–8.5)

    **Response** fields match the frontend `MOCK_RECOMMENDATIONS` constant.
    Uses Google Gemini AI for personalized advice, falls back to mock data if API key is missing.
    """
    return get_recommendations(
        location=data.location,
        nitrogen=data.nitrogen,
        phosphorus=data.phosphorus,
        potassium=data.potassium,
        ph=data.ph,
    )