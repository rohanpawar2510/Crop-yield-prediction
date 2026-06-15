"""
disease.py — POST /api/detect-disease
Saves each detection to the database.
Works for both logged-in users and guests.
"""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models.schemas import DiseaseResponse
from services.disease_service import detect_disease
from services.db_service import save_disease_detection
from routes.auth import get_optional_user

router = APIRouter()

_MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post(
    "/detect-disease",
    response_model=DiseaseResponse,
    summary="Detect plant disease from a leaf image",
)
async def disease(
    image:  UploadFile = File(..., description="Leaf image (JPEG/PNG/WebP, max 5MB)"),
    db:     Session    = Depends(get_db),
    user                = Depends(get_optional_user),
) -> DiseaseResponse:
    """
    Analyse an uploaded leaf image for signs of disease using Plant.id API.
    Saves result to database (linked to user if logged in).
    """
    image_bytes = await image.read()

    if len(image_bytes) > _MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Image too large. Maximum size is 5MB, got {len(image_bytes) // 1024}KB",
        )
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file uploaded")

    result = detect_disease(image_bytes, image.filename or "")

    # Save to DB (non-blocking — failure won't break detection)
    save_disease_detection(
        db         = db,
        result     = result,
        filename   = image.filename or "",
        image_size = len(image_bytes),
        user_id    = user.id if user else None,
    )

    return result