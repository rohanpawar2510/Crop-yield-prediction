"""
routes/predict.py — POST /api/predict
Saves each prediction to the database.
Works for both logged-in users and guests.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.schemas import SoilInput, PredictResponse
from services.prediction_service import predict_yield
from services.db_service import save_prediction
from routes.auth import get_optional_user

router = APIRouter()


@router.post("/predict", response_model=PredictResponse, summary="Predict crop & yield")
def predict(
    data:    SoilInput,
    db:      Session = Depends(get_db),
    user     = Depends(get_optional_user),
) -> PredictResponse:
    """
    Predict the best crop and expected yield.
    Saves result to database (linked to user if logged in).
    """
    result = predict_yield(
        location        = data.location,
        nitrogen        = data.nitrogen,
        phosphorus      = data.phosphorus,
        potassium       = data.potassium,
        ph              = data.ph,
        area            = data.area,
        district        = data.district,
        season          = data.season,
        irrigation_type = data.irrigation_type,
        soil_type       = data.soil_type,
        temperature     = data.temperature,
        humidity        = data.humidity,
        rainfall        = data.rainfall,
    )

    # Save to DB (non-blocking — failure doesn't break prediction)
    save_prediction(
        db              = db,
        result          = result,
        location        = data.location,
        district        = data.district,
        season          = data.season,
        nitrogen        = data.nitrogen,
        phosphorus      = data.phosphorus,
        potassium       = data.potassium,
        ph              = data.ph,
        area            = data.area,
        irrigation_type = data.irrigation_type,
        soil_type       = data.soil_type,
        temperature     = data.temperature,
        humidity        = data.humidity,
        rainfall        = data.rainfall,
        user_id         = user.id if user else None,
    )

    return result