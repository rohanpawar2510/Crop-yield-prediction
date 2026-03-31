"""
predict.py — POST /api/predict

Accepts soil / location / season parameters and returns a crop yield prediction.
"""

from fastapi import APIRouter
from models.schemas import SoilInput, PredictResponse
from services.prediction_service import predict_yield

router = APIRouter()


@router.post("/predict", response_model=PredictResponse, summary="Predict crop yield")
def predict(data: SoilInput) -> PredictResponse:
    """Predict the best crop and expected yield for given soil parameters.

    **Request body** (JSON):
    - `location`    — city/district name for weather API lookup
    - `district`    — encoded district ID (0–35, mapped from district name)
    - `season`      — encoded season ID (1=Kharif, 2=Rabi, 3=Zaid, 4=Annual)
    - `nitrogen`    — N content in kg/ha (20–150)
    - `phosphorus`  — P content in kg/ha (10–90)
    - `potassium`   — K content in kg/ha (5–150)
    - `ph`          — soil pH (5.5–8.5)
    - `area`        — cultivated area in hectares (2–416127)
    - `temperature` — air temperature in °C (auto from Weather API)
    - `humidity`    — relative humidity in % (auto from Weather API)
    - `rainfall`    — rainfall in mm (auto from Weather API)
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
        temperature=data.temperature,
        humidity=data.humidity,
        rainfall=data.rainfall,
    )