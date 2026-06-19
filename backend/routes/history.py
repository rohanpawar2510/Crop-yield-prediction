"""
routes/history.py — History endpoints.

GET  /api/history/predictions               — list user's predictions
GET  /api/history/predictions/{id}          — single prediction detail
DELETE /api/history/predictions/{id}        — delete a prediction

GET  /api/history/recommendations           — list user's recommendations
GET  /api/history/recommendations/{id}      — single recommendation detail
DELETE /api/history/recommendations/{id}    — delete a recommendation

GET  /api/history/disease                   — list disease detections
GET  /api/history/disease/{id}              — single disease detection
DELETE /api/history/disease/{id}            — delete disease detection

GET  /api/history/stats                     — user statistics summary
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models.db_models import (
    Prediction,
    Recommendation,
    DiseaseDetection,
)
from routes.auth import get_current_user

router = APIRouter()


# ─── Prediction Schemas ───────────────────────────────────────────────────────

class PredictionSummary(BaseModel):
    id: int
    location: Optional[str]
    recommended_crop: str
    confidence: float
    predicted_yield: float

    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    area: float

    temperature: Optional[float]
    humidity: Optional[float]
    rainfall: Optional[float]

    created_at: str

    model_config = {"from_attributes": True}


class PredictionDetail(PredictionSummary):
    top_3_predictions: Optional[list]
    yield_comparison: Optional[list]
    model_accuracy: Optional[float]

    district: Optional[int]
    season: Optional[int]
    irrigation_type: Optional[int]
    soil_type: Optional[int]


# ─── Recommendation Schemas ───────────────────────────────────────────────────

class RecommendationSummary(BaseModel):
    id: int
    crop: str
    location: Optional[str]
    season: Optional[str]

    soil_health_score: Optional[int]
    soil_health_label: Optional[str]
    expected_yield_boost: Optional[str]

    created_at: str

    model_config = {"from_attributes": True}


class RecommendationDetail(RecommendationSummary):
    nitrogen: Optional[float]
    phosphorus: Optional[float]
    potassium: Optional[float]
    ph: Optional[float]
    area: Optional[float]

    npk_status: Optional[dict]
    primary_fertilizer: Optional[dict]
    secondary_fertilizer: Optional[dict]

    micronutrients: Optional[list]
    application_schedule: Optional[list]
    organic_alternatives: Optional[list]
    warnings: Optional[list]

    crop_rotation: Optional[str]
    crop_rotation_reason: Optional[str]

    irrigation_advice: Optional[str]
    pest_risk: Optional[str]
    general_tips: Optional[str]


# ─── Disease Detection Schemas ────────────────────────────────────────────────

class DiseaseSummary(BaseModel):
    id: int
    filename: Optional[str]

    plant_name: Optional[str]
    is_healthy: bool

    detected: bool
    disease: Optional[str]
    confidence: Optional[int]
    severity: Optional[str]

    created_at: str

    model_config = {"from_attributes": True}


class DiseaseDetail(DiseaseSummary):
    affected_area: Optional[str]

    treatment: Optional[str]
    biological_treatment: Optional[str]
    chemical_treatment: Optional[str]
    prevention: Optional[str]

    all_diseases: Optional[list]

    image_size: Optional[int]


# ─── Stats Schema ─────────────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    total_predictions:        int
    total_recommendations:    int
    total_disease_detections: int           # ← separate from recommendations
    most_predicted_crop:      Optional[str]
    avg_confidence:           Optional[float]
    avg_yield:                Optional[float]
    last_prediction_at:       Optional[str]


# ─── Prediction Endpoints ─────────────────────────────────────────────────────

@router.get("/history/predictions", response_model=List[PredictionSummary])
def list_predictions(
    limit: int = 20,
    offset: int = 0,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Prediction)
        .filter(Prediction.user_id == user.id)
        .order_by(Prediction.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        PredictionSummary(
            id=r.id,
            location=r.location,

            recommended_crop=r.recommended_crop,
            confidence=r.confidence,
            predicted_yield=r.predicted_yield,

            nitrogen=r.nitrogen,
            phosphorus=r.phosphorus,
            potassium=r.potassium,
            ph=r.ph,
            area=r.area,

            temperature=r.temperature,
            humidity=r.humidity,
            rainfall=r.rainfall,

            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.get("/history/predictions/{prediction_id}", response_model=PredictionDetail)
def get_prediction(
    prediction_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == user.id,
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="Prediction not found")

    return PredictionDetail(
        id=row.id,
        location=row.location,

        recommended_crop=row.recommended_crop,
        confidence=row.confidence,
        predicted_yield=row.predicted_yield,

        nitrogen=row.nitrogen,
        phosphorus=row.phosphorus,
        potassium=row.potassium,
        ph=row.ph,
        area=row.area,

        temperature=row.temperature,
        humidity=row.humidity,
        rainfall=row.rainfall,

        top_3_predictions=row.top_3_predictions,
        yield_comparison=row.yield_comparison,
        model_accuracy=row.model_accuracy,

        district=row.district,
        season=row.season,
        irrigation_type=row.irrigation_type,
        soil_type=row.soil_type,

        created_at=row.created_at.isoformat(),
    )


@router.delete("/history/predictions/{prediction_id}", status_code=204)
def delete_prediction(
    prediction_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.query(Prediction).filter(
        Prediction.id == prediction_id,
        Prediction.user_id == user.id,
    ).first()

    if not row:
        raise HTTPException(status_code=404, detail="Prediction not found")

    db.delete(row)
    db.commit()


# ─── Recommendation Endpoints ─────────────────────────────────────────────────

@router.get("/history/recommendations", response_model=List[RecommendationSummary])
def list_recommendations(
    limit: int = 20,
    offset: int = 0,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user.id)
        .order_by(Recommendation.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        RecommendationSummary(
            id=r.id,
            crop=r.crop,
            location=r.location,
            season=r.season,

            soil_health_score=r.soil_health_score,
            soil_health_label=r.soil_health_label,
            expected_yield_boost=r.expected_yield_boost,

            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.get("/history/recommendations/{rec_id}", response_model=RecommendationDetail)
def get_recommendation(
    rec_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(Recommendation).filter(
        Recommendation.id == rec_id,
        Recommendation.user_id == user.id,
    ).first()

    if not r:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return RecommendationDetail(
        id=r.id,
        crop=r.crop,
        location=r.location,
        season=r.season,

        soil_health_score=r.soil_health_score,
        soil_health_label=r.soil_health_label,
        expected_yield_boost=r.expected_yield_boost,

        created_at=r.created_at.isoformat(),

        nitrogen=r.nitrogen,
        phosphorus=r.phosphorus,
        potassium=r.potassium,
        ph=r.ph,
        area=r.area,

        npk_status=r.npk_status,
        primary_fertilizer=r.primary_fertilizer,
        secondary_fertilizer=r.secondary_fertilizer,

        micronutrients=r.micronutrients,
        application_schedule=r.application_schedule,
        organic_alternatives=r.organic_alternatives,
        warnings=r.warnings,

        crop_rotation=r.crop_rotation,
        crop_rotation_reason=r.crop_rotation_reason,

        irrigation_advice=r.irrigation_advice,
        pest_risk=r.pest_risk,
        general_tips=r.general_tips,
    )


@router.delete("/history/recommendations/{rec_id}", status_code=204)
def delete_recommendation(
    rec_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(Recommendation).filter(
        Recommendation.id == rec_id,
        Recommendation.user_id == user.id,
    ).first()

    if not r:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    db.delete(r)
    db.commit()


# ─── Disease Detection Endpoints ──────────────────────────────────────────────

@router.get("/history/disease", response_model=List[DiseaseSummary])
def list_disease_detections(
    limit: int = 20,
    offset: int = 0,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(DiseaseDetection)
        .filter(DiseaseDetection.user_id == user.id)
        .order_by(DiseaseDetection.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [
        DiseaseSummary(
            id=r.id,
            filename=r.filename,

            plant_name=r.plant_name,
            is_healthy=r.is_healthy,

            detected=r.detected,
            disease=r.disease,
            confidence=r.confidence,
            severity=r.severity,

            created_at=r.created_at.isoformat(),
        )
        for r in rows
    ]


@router.get("/history/disease/{det_id}", response_model=DiseaseDetail)
def get_disease_detection(
    det_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(DiseaseDetection).filter(
        DiseaseDetection.id == det_id,
        DiseaseDetection.user_id == user.id,
    ).first()

    if not r:
        raise HTTPException(status_code=404, detail="Detection not found")

    return DiseaseDetail(
        id=r.id,
        filename=r.filename,

        plant_name=r.plant_name,
        is_healthy=r.is_healthy,

        detected=r.detected,
        disease=r.disease,
        confidence=r.confidence,
        severity=r.severity,

        affected_area=r.affected_area,

        treatment=r.treatment,
        biological_treatment=r.biological_treatment,
        chemical_treatment=r.chemical_treatment,
        prevention=r.prevention,

        all_diseases=r.all_diseases,

        image_size=r.image_size,

        created_at=r.created_at.isoformat(),
    )


@router.delete("/history/disease/{det_id}", status_code=204)
def delete_disease_detection(
    det_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    r = db.query(DiseaseDetection).filter(
        DiseaseDetection.id == det_id,
        DiseaseDetection.user_id == user.id,
    ).first()

    if not r:
        raise HTTPException(status_code=404, detail="Detection not found")

    db.delete(r)
    db.commit()


# ─── Stats ────────────────────────────────────────────────────────────────────

@router.get("/history/stats", response_model=StatsResponse)
def get_stats(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preds = db.query(Prediction).filter(
        Prediction.user_id == user.id
    ).all()

    recs = db.query(Recommendation).filter(
        Recommendation.user_id == user.id
    ).all()

    diseases = db.query(DiseaseDetection).filter(
        DiseaseDetection.user_id == user.id
    ).all()

    if preds:
        crop_counts = {}
        for p in preds:
            crop_counts[p.recommended_crop] = (
                crop_counts.get(p.recommended_crop, 0) + 1
            )

        most_predicted = max(crop_counts, key=crop_counts.get)
        avg_conf       = round(sum(p.confidence for p in preds) / len(preds), 2)
        avg_yield      = round(sum(p.predicted_yield for p in preds) / len(preds), 4)
        last_at        = max(p.created_at for p in preds).isoformat()
    else:
        most_predicted = None
        avg_conf       = None
        avg_yield      = None
        last_at        = None

    return StatsResponse(
        total_predictions        = len(preds),
        total_recommendations    = len(recs),       # ← only AI recommendations
        total_disease_detections = len(diseases),   # ← separate disease count
        most_predicted_crop      = most_predicted,
        avg_confidence           = avg_conf,
        avg_yield                = avg_yield,
        last_prediction_at       = last_at,
    )