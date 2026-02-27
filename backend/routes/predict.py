"""
predict.py — POST /api/predict

Accepts soil / location parameters and returns a crop yield prediction.
"""

from fastapi import APIRouter
from models.schemas import SoilInput, PredictResponse
from services.prediction_service import predict_yield

router = APIRouter()


@router.post("/predict", response_model=PredictResponse, summary="Predict crop yield")
def predict(data: SoilInput) -> PredictResponse:
    """Predict the best crop and expected yield for given soil parameters.

    **Request body** (JSON):
    - `location` — city or region name
    - `nitrogen` — N content in kg/ha (0–140)
    - `phosphorus` — P content in kg/ha (0–145)
    - `potassium` — K content in kg/ha (0–205)
    - `ph` — soil pH (0–14)

    **Response** fields match the frontend `MOCK_PREDICTION` constant.
    """
    return predict_yield(
        location=data.location,
        nitrogen=data.nitrogen,
        phosphorus=data.phosphorus,
        potassium=data.potassium,
        ph=data.ph,
    )
