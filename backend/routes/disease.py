"""
disease.py — POST /api/detect-disease

Accepts a multipart-form image upload and returns a disease detection result.
"""

from fastapi import APIRouter, File, UploadFile
from models.schemas import DiseaseResponse
from services.disease_service import detect_disease

router = APIRouter()


@router.post(
    "/detect-disease",
    response_model=DiseaseResponse,
    summary="Detect plant disease from a leaf image",
)
async def disease(image: UploadFile = File(..., description="Leaf image file")) -> DiseaseResponse:
    """Analyse an uploaded leaf image for signs of disease.

    **Form field**:
    - `image` — image file (JPEG / PNG)

    **Response** fields match the frontend `MOCK_DISEASE` constant.
    Phase 4 will integrate a real computer-vision model.
    """
    image_bytes = await image.read()
    return detect_disease(image_bytes, image.filename or "")
