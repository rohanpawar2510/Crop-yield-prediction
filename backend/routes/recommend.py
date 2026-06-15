"""
routes/recommend.py — POST /api/recommend
Saves each recommendation to the database.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.schemas import SoilInputRecommend, RecommendResponse
from services.recommendation_service import get_recommendations
from services.db_service import save_recommendation
from routes.auth import get_optional_user

router = APIRouter()


@router.post("/recommend", response_model=RecommendResponse,
             summary="Get AI farming recommendations")
def recommend(
    data: SoilInputRecommend,
    db:   Session = Depends(get_db),
    user  = Depends(get_optional_user),
) -> RecommendResponse:
    """
    Get crop-specific fertilizer and farming recommendations.
    Saves result to database (linked to user if logged in).
    """
    result = get_recommendations(
        location        = data.location,
        nitrogen        = data.nitrogen,
        phosphorus      = data.phosphorus,
        potassium       = data.potassium,
        ph              = data.ph,
        crop            = data.crop,
        season          = data.season,
        soil_type       = data.soil_type,
        irrigation_type = data.irrigation_type,
        area            = data.area,
        temperature     = data.temperature,
        rainfall        = data.rainfall,
        predicted_yield = data.predicted_yield,
    )

    # Save to DB
    save_recommendation(
        db              = db,
        result          = result,
        crop            = data.crop,
        location        = data.location,
        season          = data.season,
        soil_type       = data.soil_type,
        irrigation_type = data.irrigation_type,
        area            = data.area,
        nitrogen        = data.nitrogen,
        phosphorus      = data.phosphorus,
        potassium       = data.potassium,
        ph              = data.ph,
        user_id         = user.id if user else None,
    )

    return result