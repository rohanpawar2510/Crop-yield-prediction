"""
schemas.py — Pydantic request / response models for all API endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ─── Shared request body ──────────────────────────────────────────────────────

class SoilInput(BaseModel):
    """Soil / location data submitted by the user."""

    location: str = Field(default="Unknown", example="Pune, Maharashtra")
    nitrogen: float = Field(..., ge=0, le=140, example=80)
    phosphorus: float = Field(..., ge=0, le=145, example=40)
    potassium: float = Field(..., ge=0, le=205, example=60)
    ph: float = Field(..., ge=0, le=14, example=6.5)
    temperature: Optional[float] = Field(default=None, ge=0, le=50, example=25.0)
    humidity: Optional[float] = Field(default=None, ge=0, le=100, example=80.0)
    rainfall: Optional[float] = Field(default=None, ge=0, le=500, example=200.0)


# ─── POST /api/predict ────────────────────────────────────────────────────────

class PredictResponse(BaseModel):
    crop: str
    recommended_crop: str
    yield_: float = Field(..., alias="yield")
    predicted_yield: float
    unit: str
    confidence: int
    suitable_crops: List[str]
    yield_comparison: List[float]

    model_config = {"populate_by_name": True}


# ─── GET /api/weather ─────────────────────────────────────────────────────────

class WeatherResponse(BaseModel):
    location: str
    temperature: float
    humidity: float
    rainfall: float
    wind_speed: float
    description: str
    icon: str
    is_mock: bool = False
    feels_like: Optional[float] = None
    pressure: Optional[int] = None
    visibility: Optional[int] = None


# ─── POST /api/detect-disease ────────────────────────────────────────────────

class DiseaseResponse(BaseModel):
    detected: bool
    disease: str
    confidence: int
    severity: str
    affected_area: str
    treatment: str


# ─── POST /api/recommend ─────────────────────────────────────────────────────

class FertilizerDetail(BaseModel):
    primary: str
    amount: str
    schedule: str
    alternatives: List[str]
    distribution: Dict[str, Any]


class RecommendResponse(BaseModel):
    fertilizer: FertilizerDetail
    crop_rotation: str
    irrigation: str
    pest_management: str
    general: str


# ─── GET /health ──────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str


# ─── GET / ────────────────────────────────────────────────────────────────────

class RootResponse(BaseModel):
    message: str
    version: str
    routes: List[str]
