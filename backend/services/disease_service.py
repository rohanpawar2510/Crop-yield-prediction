"""
disease_service.py — Plant disease detection from leaf images.

Phase 4 will replace the mock below with a real image-classification model.
"""

from __future__ import annotations

from models.schemas import DiseaseResponse


# Mock response — matches MOCK_DISEASE in frontend/js/api.js
_MOCK: dict = {
    "detected": True,
    "disease": "Leaf Blight",
    "confidence": 87,
    "severity": "Moderate",
    "affected_area": "35%",
    "treatment": (
        "Apply copper-based fungicide. "
        "Remove and destroy infected leaves. "
        "Ensure proper spacing between plants for air circulation."
    ),
}


def detect_disease(image_bytes: bytes, filename: str) -> DiseaseResponse:
    """Analyse a leaf image and return a disease detection result.

    Args:
        image_bytes: Raw bytes of the uploaded image file.
        filename: Original filename (used for MIME-type checks in Phase 4).

    Returns:
        DiseaseResponse with mock data until the CV model is integrated.
    """
    # TODO (Phase 4): run image through the disease-detection model.
    return DiseaseResponse(**_MOCK)
