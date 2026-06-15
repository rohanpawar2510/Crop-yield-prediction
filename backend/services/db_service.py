"""
services/db_service.py — Save predictions and recommendations to the database.

Called from predict route and recommend route after successful API responses.
user_id is optional — guest users (not logged in) still get predictions,
they just won't appear in history.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from models.db_models import Prediction, Recommendation, DiseaseDetection
from models.schemas import PredictResponse, RecommendResponse

logger = logging.getLogger(__name__)


def save_prediction(
    db: Session,
    result: PredictResponse,

    # Raw inputs
    location: str,
    district: int,
    season: int,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph: float,
    area: float,
    irrigation_type: int,
    soil_type: int,
    temperature: Optional[float],
    humidity: Optional[float],
    rainfall: Optional[float],
    user_id: Optional[int] = None,
) -> Optional[Prediction]:
    """Save a prediction result to the database. Returns saved row."""

    try:
        row = Prediction(
            user_id=user_id,
            location=location,
            district=district,
            season=season,

            nitrogen=nitrogen,
            phosphorus=phosphorus,
            potassium=potassium,
            ph=ph,
            area=area,

            irrigation_type=irrigation_type,
            soil_type=soil_type,

            temperature=temperature,
            humidity=humidity,
            rainfall=rainfall,

            recommended_crop=result.recommended_crop,
            confidence=result.confidence,
            predicted_yield=result.predicted_yield,

            top_3_predictions=[
                {"crop": p.crop, "confidence": p.confidence}
                for p in (result.top_3_predictions or [])
            ],

            yield_comparison=result.yield_comparison,
            model_accuracy=result.model_accuracy,
        )

        db.add(row)
        db.commit()
        db.refresh(row)

        logger.info(
            "✅ Prediction saved — id=%d crop=%s user=%s",
            row.id,
            row.recommended_crop,
            user_id
        )

        return row

    except Exception as exc:
        db.rollback()
        logger.error("Failed to save prediction: %s", exc)
        return None


def save_recommendation(
    db: Session,
    result: dict,

    crop: str,
    location: str,
    season: str,
    soil_type: str,
    irrigation_type: str,
    area: float,

    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph: float,

    user_id: Optional[int] = None,
    prediction_id: Optional[int] = None,
) -> Optional[Recommendation]:
    """Save a recommendation result to the database. Returns saved row."""

    try:
        row = Recommendation(
            user_id=user_id,
            prediction_id=prediction_id,

            crop=crop,
            location=location,
            season=season,
            soil_type=soil_type,
            irrigation_type=irrigation_type,
            area=area,

            nitrogen=nitrogen,
            phosphorus=phosphorus,
            potassium=potassium,
            ph=ph,

            soil_health_score=result.get("soil_health_score"),
            soil_health_label=result.get("soil_health_label"),

            npk_status=result.get("npk_status"),
            primary_fertilizer=result.get("primary_fertilizer"),
            secondary_fertilizer=result.get("secondary_fertilizer"),
            micronutrients=result.get("micronutrients"),

            application_schedule=result.get("application_schedule"),
            organic_alternatives=result.get("organic_alternatives"),
            warnings=result.get("warnings"),

            crop_rotation=result.get("crop_rotation"),
            crop_rotation_reason=result.get("crop_rotation_reason"),

            expected_yield_boost=result.get("expected_yield_boost"),
            irrigation_advice=result.get("irrigation_advice"),
            pest_risk=result.get("pest_risk"),
            general_tips=result.get("general_tips"),
        )

        db.add(row)
        db.commit()
        db.refresh(row)

        logger.info(
            "✅ Recommendation saved — id=%d crop=%s user=%s",
            row.id,
            crop,
            user_id
        )

        return row

    except Exception as exc:
        db.rollback()
        logger.error("Failed to save recommendation: %s", exc)
        return None


def save_disease_detection(
    db: Session,
    result,
    filename: str = "",
    image_size: int = 0,
    user_id: Optional[int] = None,
):
    """Save disease detection result to database."""

    try:
        row = DiseaseDetection(
            user_id=user_id,

            filename=filename,
            image_size=image_size,

            plant_name=getattr(result, "plant_name", None),
            is_healthy=getattr(result, "is_healthy", False),

            detected=result.detected,
            disease=result.disease,
            confidence=result.confidence,
            severity=result.severity,
            affected_area=result.affected_area,

            treatment=result.treatment,
            biological_treatment=getattr(result, "biological_treatment", None),
            chemical_treatment=getattr(result, "chemical_treatment", None),
            prevention=getattr(result, "prevention", None),

            all_diseases=getattr(result, "all_diseases", []),
        )

        db.add(row)
        db.commit()
        db.refresh(row)

        logger.info(
            "✅ Disease detection saved — id=%d disease=%s user=%s",
            row.id,
            row.disease,
            user_id
        )

        return row

    except Exception as exc:
        db.rollback()
        logger.error("Failed to save disease detection: %s", exc)
        return None