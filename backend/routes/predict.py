"""
predict.py — POST /api/predict
"""

from fastapi import APIRouter
from models.schemas import SoilInput, PredictResponse
from services.prediction_service import predict_yield

router = APIRouter()


@router.post("/predict", response_model=PredictResponse, summary="Predict crop & yield")
def predict(data: SoilInput) -> PredictResponse:
    """
    Predict the best crop and expected yield.

    Request body:
    - location, district, season       — location inputs
    - nitrogen, phosphorus, potassium  — soil nutrients (kg/ha)
    - ph, area                         — soil conditions
    - irrigation_type                  — 0=Rainfed,1=Canal,2=Drip,3=Flood,4=Sprinkler
    - soil_type                        — 0=Black,1=Alluvial,2=Sandy,3=Loamy,4=Clayey
    - temperature, humidity, rainfall  — auto from Weather API
    """
    return predict_yield(
        location=data.location,
        nitrogen=data.nitrogen,
        phosphorus=data.phosphorus,
        potassium=data.potassium,
        ph=data.ph,
        area=data.area,
        district=data.district,
        season=data.season,
        irrigation_type=data.irrigation_type,
        soil_type=data.soil_type,
        temperature=data.temperature,
        humidity=data.humidity,
        rainfall=data.rainfall,
    )