"""
models/db_models.py — Database ORM models.

Tables:
  users           — registered farmers
  predictions     — crop + yield prediction history
  recommendations — AI fertilizer recommendation history
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column, Integer, Float, String, Boolean,
    DateTime, ForeignKey, Text, JSON,
)
from sqlalchemy.orm import relationship

from database import Base


# ─── User ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    email         = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    district      = Column(String(100), nullable=True)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    predictions     = relationship("Prediction",     back_populates="user", cascade="all, delete")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete")
    disease_detections = relationship("DiseaseDetection", back_populates="user", cascade="all, delete")

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


# ─── Prediction ───────────────────────────────────────────────────────────────

class Prediction(Base):
    __tablename__ = "predictions"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable for guest users

    # Location
    location   = Column(String(100), nullable=True)
    district   = Column(Integer, nullable=True)
    season     = Column(Integer, nullable=True)

    # Soil inputs
    nitrogen   = Column(Float, nullable=False)
    phosphorus = Column(Float, nullable=False)
    potassium  = Column(Float, nullable=False)
    ph         = Column(Float, nullable=False)
    area       = Column(Float, nullable=False)

    # Farm conditions
    irrigation_type = Column(Integer, default=0)
    soil_type       = Column(Integer, default=0)

    # Weather at time of prediction
    temperature = Column(Float, nullable=True)
    humidity    = Column(Float, nullable=True)
    rainfall    = Column(Float, nullable=True)

    # Results
    recommended_crop  = Column(String(50), nullable=False)
    confidence        = Column(Float, nullable=False)
    predicted_yield   = Column(Float, nullable=False)
    top_3_predictions = Column(JSON, nullable=True)   # list of {crop, confidence}
    yield_comparison  = Column(JSON, nullable=True)   # list of floats
    model_accuracy    = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user            = relationship("User", back_populates="predictions")
    recommendations = relationship("Recommendation", back_populates="prediction", cascade="all, delete")

    def __repr__(self):
        return f"<Prediction id={self.id} crop={self.recommended_crop} yield={self.predicted_yield}>"


# ─── Recommendation ───────────────────────────────────────────────────────────

class Recommendation(Base):
    __tablename__ = "recommendations"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)

    # Context
    crop            = Column(String(50), nullable=False)
    location        = Column(String(100), nullable=True)
    season          = Column(String(50), nullable=True)
    soil_type       = Column(String(50), nullable=True)
    irrigation_type = Column(String(50), nullable=True)
    area            = Column(Float, nullable=True)

    # Soil inputs at time of recommendation
    nitrogen   = Column(Float, nullable=True)
    phosphorus = Column(Float, nullable=True)
    potassium  = Column(Float, nullable=True)
    ph         = Column(Float, nullable=True)

    # Results (stored as JSON)
    soil_health_score    = Column(Integer, nullable=True)
    soil_health_label    = Column(String(20), nullable=True)
    npk_status           = Column(JSON, nullable=True)
    primary_fertilizer   = Column(JSON, nullable=True)
    secondary_fertilizer = Column(JSON, nullable=True)
    micronutrients       = Column(JSON, nullable=True)
    application_schedule = Column(JSON, nullable=True)
    organic_alternatives = Column(JSON, nullable=True)
    warnings             = Column(JSON, nullable=True)
    crop_rotation        = Column(String(100), nullable=True)
    crop_rotation_reason = Column(Text, nullable=True)
    expected_yield_boost = Column(String(20), nullable=True)
    irrigation_advice    = Column(Text, nullable=True)
    pest_risk            = Column(Text, nullable=True)
    general_tips         = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user       = relationship("User",       back_populates="recommendations")
    prediction = relationship("Prediction", back_populates="recommendations")

    def __repr__(self):
        return f"<Recommendation id={self.id} crop={self.crop}>"
# ─── Disease Detection ────────────────────────────────────────────────────────

class DiseaseDetection(Base):
    __tablename__ = "disease_detections"

    id       = Column(Integer, primary_key=True, index=True)
    user_id  = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Image info
    filename   = Column(String(255), nullable=True)
    image_size = Column(Integer, nullable=True)

    # Plant identification
    plant_name = Column(String(100), nullable=True)
    is_healthy = Column(Boolean, default=False)

    # Primary disease result
    detected      = Column(Boolean, default=False)
    disease       = Column(String(150), nullable=True)
    confidence    = Column(Integer, nullable=True)
    severity      = Column(String(50), nullable=True)
    affected_area = Column(String(50), nullable=True)

    # Treatments
    treatment            = Column(Text, nullable=True)
    biological_treatment = Column(Text, nullable=True)
    chemical_treatment   = Column(Text, nullable=True)
    prevention           = Column(Text, nullable=True)

    # All diseases detected
    all_diseases = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    user = relationship("User", back_populates="disease_detections")

    def __repr__(self):
        return f"<DiseaseDetection id={self.id} disease={self.disease}>"