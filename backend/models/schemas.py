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

SEASON_MAP: dict[str, int] = {
    "Kharif (June – Oct)": 1,
    "Rabi (Nov – Mar)":    2,
    "Zaid (Mar – Jun)":    3,
    "Annual":              4,
}

IRRIGATION_MAP: dict[str, int] = {
    "Rainfed":   0,
    "Canal":     1,
    "Drip":      2,
    "Flood":     3,
    "Sprinkler": 4,
}

SOIL_MAP: dict[str, int] = {
    "Black":    0,
    "Alluvial": 1,
    "Sandy":    2,
    "Loamy":    3,
    "Clayey":   4,
}


# ─── POST /api/predict ────────────────────────────────────────────────────────

class SoilInput(BaseModel):
    location:        str   = Field(default="Unknown", example="Pune")
    district:        int   = Field(..., ge=0,  le=35,   example=25)
    season:          int   = Field(..., ge=1,  le=4,    example=1)
    nitrogen:        float = Field(..., ge=20, le=150,  example=90)
    phosphorus:      float = Field(..., ge=10, le=90,   example=42)
    potassium:       float = Field(..., ge=5,  le=150,  example=43)
    ph:              float = Field(..., ge=5.5,le=8.5,  example=6.5)
    area:            float = Field(..., ge=2,  le=416127,example=15000)
    irrigation_type: int   = Field(default=0, ge=0, le=4)
    soil_type:       int   = Field(default=0, ge=0, le=4)
    temperature:     Optional[float] = Field(default=None, ge=10,  le=40)
    humidity:        Optional[float] = Field(default=None, ge=0,   le=100)
    rainfall:        Optional[float] = Field(default=None, ge=0,   le=2000)


class CropPrediction(BaseModel):
    crop:       str
    confidence: float


class PredictResponse(BaseModel):
    location:          str                  = Field(default="Unknown")
    crop:              str
    recommended_crop:  str
    confidence:        float
    top_3_predictions: List[CropPrediction] = Field(default_factory=list)
    suitable_crops:    List[str]            = Field(default_factory=list)
    model_accuracy:    Optional[float]      = None
    yield_:            float                = Field(default=0.0, alias="yield")
    predicted_yield:   float                = Field(default=0.0)
    unit:              str                  = Field(default="tons/hectare")
    yield_comparison:  List[float]          = Field(default_factory=list)

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
    # Core fields
    detected:      bool
    disease:       str
    confidence:    int
    severity:      str
    affected_area: str
    treatment:     str
    is_mock:       bool = False
    # Rich fields from Plant.id API
    plant_name:           str             = Field(default='')
    is_healthy:           bool            = Field(default=False)
    all_diseases:         List[Dict[str, Any]] = Field(default_factory=list)
    prevention:           str             = Field(default='')
    biological_treatment: str             = Field(default='')
    chemical_treatment:   str             = Field(default='')


# ─── POST /api/recommend ─────────────────────────────────────────────────────
# Updated with crop context fields for professional Gemini recommendations

class SoilInputRecommend(BaseModel):
    """Input for /api/recommend — includes crop context from prediction result."""
    # Core soil inputs
    location:        str   = Field(...,          example="Pune")
    nitrogen:        float = Field(..., ge=20,   le=150, example=90)
    phosphorus:      float = Field(..., ge=10,   le=90,  example=42)
    potassium:       float = Field(..., ge=5,    le=150, example=43)
    ph:              float = Field(..., ge=5.5,  le=8.5, example=6.5)
    # Crop context — passed from prediction result
    crop:            str   = Field(default="Unknown", example="SUGARCANE")
    season:          str   = Field(default="Kharif",  example="Annual")
    soil_type:       str   = Field(default="Black",   example="Black")
    irrigation_type: str   = Field(default="Rainfed", example="Drip")
    area:            float = Field(default=1.0,        example=50000)
    temperature:     float = Field(default=25.0,       example=30.0)
    rainfall:        float = Field(default=800.0,      example=1200.0)
    predicted_yield: float = Field(default=0.0,        example=10.5)


class RecommendResponse(BaseModel):
    """Professional recommendation response — 15 fields from Gemini AI."""
    soil_health_score:    int                  = Field(default=70)
    soil_health_label:    str                  = Field(default="Good")
    npk_status:           Dict[str, Any]       = Field(default_factory=dict)
    primary_fertilizer:   Dict[str, Any]       = Field(default_factory=dict)
    secondary_fertilizer: Dict[str, Any]       = Field(default_factory=dict)
    micronutrients:       List[Dict[str, Any]] = Field(default_factory=list)
    application_schedule: List[Dict[str, Any]] = Field(default_factory=list)
    organic_alternatives: List[Dict[str, Any]] = Field(default_factory=list)
    warnings:             List[str]            = Field(default_factory=list)
    crop_rotation:        str                  = Field(default="")
    crop_rotation_reason: str                  = Field(default="")
    expected_yield_boost: str                  = Field(default="")
    irrigation_advice:    str                  = Field(default="")
    pest_risk:            str                  = Field(default="")
    general_tips:         str                  = Field(default="")


# ─── GET /health ──────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status:  str
    version: str


# ─── GET / ────────────────────────────────────────────────────────────────────

class RootResponse(BaseModel):
    message: str
    version: str
    routes:  List[str]