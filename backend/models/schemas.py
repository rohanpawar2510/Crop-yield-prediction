"""
schemas.py — Pydantic request / response models for all API endpoints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ─── District name → encoded ID ──────────────────────────────────────────────

DISTRICT_MAP: dict[str, int] = {
    "Ahmednagar": 0,  "Akola": 1,       "Amravati": 2,    "Aurangabad": 3,
    "Beed": 4,        "Bhandara": 5,    "Buldhana": 6,    "Chandrapur": 7,
    "Dhule": 8,       "Gadchiroli": 9,  "Gondia": 10,     "Hingoli": 11,
    "Jalgaon": 12,    "Jalna": 13,      "Kolhapur": 14,   "Latur": 15,
    "Mumbai": 17,     "Nagpur": 18,     "Nanded": 19,     "Nandurbar": 20,
    "Nashik": 21,     "Osmanabad": 22,  "Palghar": 23,    "Parbhani": 24,
    "Pune": 25,       "Raigad": 26,     "Ratnagiri": 27,  "Sangli": 28,
    "Satara": 29,     "Sindhudurg": 30, "Solapur": 31,    "Thane": 32,
    "Wardha": 33,     "Washim": 34,     "Yavatmal": 35,
}

# ─── Season name → encoded ID ─────────────────────────────────────────────────

SEASON_MAP: dict[str, int] = {
    "Kharif (June – Oct)": 1,
    "Rabi (Nov – Mar)":    2,
    "Zaid (Mar – Jun)":    3,
    "Annual":              4,
}

# ─── Irrigation type → encoded ID ─────────────────────────────────────────────

IRRIGATION_MAP: dict[str, int] = {
    "Rainfed":   0,
    "Canal":     1,
    "Drip":      2,
    "Flood":     3,
    "Sprinkler": 4,
}

# ─── Soil type → encoded ID ───────────────────────────────────────────────────

SOIL_MAP: dict[str, int] = {
    "Black":    0,
    "Alluvial": 1,
    "Sandy":    2,
    "Loamy":    3,
    "Clayey":   4,
}


# ─── Shared request body ──────────────────────────────────────────────────────

class SoilInput(BaseModel):
    """Soil / location / season / irrigation data submitted by the user."""

    # ── Location & season ──
    location:   str = Field(default="Unknown", example="Pune")
    district:   int = Field(..., ge=0,  le=35,  example=25,
                            description="Encoded district ID (0–35)")
    season:     int = Field(..., ge=1,  le=4,   example=1,
                            description="1=Kharif, 2=Rabi, 3=Zaid, 4=Annual")

    # ── Soil nutrients ──
    nitrogen:   float = Field(..., ge=20,  le=150,    example=90)
    phosphorus: float = Field(..., ge=10,  le=90,     example=42)
    potassium:  float = Field(..., ge=5,   le=150,    example=43)
    ph:         float = Field(..., ge=5.5, le=8.5,    example=6.5)
    area:       float = Field(..., ge=2,   le=416127, example=15000)

    # ── New yield model inputs ──
    irrigation_type: int = Field(
        default=0, ge=0, le=4, example=0,
        description="0=Rainfed, 1=Canal, 2=Drip, 3=Flood, 4=Sprinkler"
    )
    soil_type: int = Field(
        default=0, ge=0, le=4, example=0,
        description="0=Black, 1=Alluvial, 2=Sandy, 3=Loamy, 4=Clayey"
    )

    # ── Weather (auto-fetched from OpenWeather API) ──
    temperature: Optional[float] = Field(default=None, ge=10,  le=40,   example=37.3)
    humidity:    Optional[float] = Field(default=None, ge=0,   le=100,  example=22.0)
    rainfall:    Optional[float] = Field(default=None, ge=0,   le=2000, example=0.0)


# ─── POST /api/predict ────────────────────────────────────────────────────────

class CropPrediction(BaseModel):
    crop:       str
    confidence: float


class PredictResponse(BaseModel):
    location:          str              = Field(default="Unknown")
    crop:              str
    recommended_crop:  str
    confidence:        float
    top_3_predictions: List[CropPrediction] = Field(default_factory=list)
    suitable_crops:    List[str]            = Field(default_factory=list)
    model_accuracy:    Optional[float]      = None
    yield_:            float       = Field(default=0.0, alias="yield")
    predicted_yield:   float       = Field(default=0.0)
    unit:              str         = Field(default="tons/hectare")
    yield_comparison:  List[float] = Field(default_factory=list)

    model_config = {"populate_by_name": True, "protected_namespaces": ()}


# ─── GET /api/weather ─────────────────────────────────────────────────────────

class WeatherResponse(BaseModel):
    location:    str
    temperature: float
    humidity:    float
    rainfall:    float
    wind_speed:  float
    description: str
    icon:        str
    is_mock:     bool            = False
    feels_like:  Optional[float] = None
    pressure:    Optional[int]   = None
    visibility:  Optional[int]   = None


# ─── POST /api/detect-disease ────────────────────────────────────────────────

class DiseaseResponse(BaseModel):
    detected:      bool
    disease:       str
    confidence:    int
    severity:      str
    affected_area: str
    treatment:     str
    is_mock:       bool = False


# ─── POST /api/recommend ─────────────────────────────────────────────────────

class SoilInputRecommend(BaseModel):
    location:   str   = Field(..., example="Pune")
    nitrogen:   float = Field(..., ge=20,  le=150, example=90)
    phosphorus: float = Field(..., ge=10,  le=90,  example=42)
    potassium:  float = Field(..., ge=5,   le=150, example=43)
    ph:         float = Field(..., ge=5.5, le=8.5, example=6.5)


class FertilizerDetail(BaseModel):
    primary:      str
    amount:       str
    schedule:     str
    alternatives: List[str]
    distribution: Dict[str, Any]


class RecommendResponse(BaseModel):
    fertilizer:      FertilizerDetail
    crop_rotation:   str
    irrigation:      str
    pest_management: str
    general:         str


# ─── GET /health ──────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:  str
    version: str


# ─── GET / ────────────────────────────────────────────────────────────────────

class RootResponse(BaseModel):
    message: str
    version: str
    routes:  List[str]