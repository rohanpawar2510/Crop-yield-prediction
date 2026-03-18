"""
disease_service.py — Plant disease detection from leaf images.

Calls the Plant.id API (https://plant.id) for real disease identification.
Falls back to mock data when the API key is unavailable or the request fails.
"""

from __future__ import annotations

import base64
import logging
import mimetypes

import httpx
from fastapi import HTTPException

import config
from models.schemas import DiseaseResponse

logger = logging.getLogger(__name__)

# Seconds to wait for the Plant.id API to respond
_API_TIMEOUT: int = 30

# Supported image MIME types
_ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)

# Mock response — fallback when the API call fails or key is missing
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


def _get_mime_type(filename: str, image_bytes: bytes) -> str:
    """Determine the MIME type of the uploaded image.

    Tries the filename extension first, then falls back to magic-byte detection.
    """
    if filename:
        mime, _ = mimetypes.guess_type(filename)
        if mime and mime in _ALLOWED_MIME_TYPES:
            return mime

    # Magic-byte detection
    if image_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"

    return "image/jpeg"  # best-effort fallback


def _build_treatment(disease_data: dict) -> str:
    """Build a human-readable treatment string from Plant.id disease details."""
    treatment_obj = disease_data.get("treatment", {})
    if not treatment_obj:
        return _MOCK["treatment"]

    parts: list[str] = []
    if biological := treatment_obj.get("biological"):
        parts.append(f"Biological: {biological}")
    if chemical := treatment_obj.get("chemical"):
        parts.append(f"Chemical: {chemical}")
    if prevention := treatment_obj.get("prevention"):
        parts.append(f"Prevention: {prevention}")

    return " | ".join(parts) if parts else _MOCK["treatment"]


def _affected_area_from_severity(severity: str) -> str:
    """Estimate an affected-area range from a severity label."""
    if severity == "High":
        return ">50%"
    if severity == "Moderate":
        return "25–50%"
    return "<25%"


def _severity_from_probability(probability: float) -> str:
    """Map a disease probability (0–1) to a severity label."""
    if probability >= 0.8:
        return "High"
    if probability >= 0.5:
        return "Moderate"
    return "Low"


def detect_disease(image_bytes: bytes, filename: str) -> DiseaseResponse:
    """Analyse a leaf image and return a disease detection result.

    Calls the Plant.id API when ``PLANT_ID_API_KEY`` is configured.
    Falls back to mock data on network/API errors so the frontend always
    receives a response.  A missing or misconfigured API key raises a 503
    immediately so operators know the service needs to be configured.

    Args:
        image_bytes: Raw bytes of the uploaded image file.
        filename: Original filename — used for MIME-type detection.

    Returns:
        DiseaseResponse with real or mock disease detection data.

    Raises:
        HTTPException 400: Empty image or unsupported format.
        HTTPException 503: Plant.id API key is not configured.
    """
    if not image_bytes:
        raise HTTPException(status_code=400, detail="No image data provided")

    mime_type = _get_mime_type(filename, image_bytes)
    if mime_type not in _ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid image format. Supported formats: JPEG, PNG, WebP, GIF",
        )

    if not config.PLANT_ID_API_KEY:
        raise HTTPException(
            status_code=503,
            detail=(
                "Disease detection service unavailable: "
                "PLANT_ID_API_KEY is not configured"
            ),
        )

    # Encode image as a base64 data URI expected by the Plant.id API
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:{mime_type};base64,{b64_image}"

    payload = {
        "images": [data_uri],
        "modifiers": ["similar_images"],
        "plant_language": "en",
        "disease_details": [
            "cause",
            "common_names",
            "classification",
            "description",
            "treatment",
            "url",
        ],
    }
    headers = {
        "Content-Type": "application/json",
        "Api-Key": config.PLANT_ID_API_KEY,
    }

    try:
        response = httpx.post(
            config.PLANT_ID_API_URL,
            json=payload,
            headers=headers,
            timeout=_API_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        health: dict = data.get("health_assessment", {})
        diseases: list[dict] = health.get("diseases", [])

        if not diseases:
            healthy_probability: float = float(health.get("is_healthy_probability", 1.0))
            return DiseaseResponse(
                detected=False,
                disease="No disease detected",
                confidence=int(healthy_probability * 100),
                severity="None",
                affected_area="0%",
                treatment="No treatment required. Keep monitoring the plant.",
            )

        top_disease = diseases[0]
        probability: float = float(top_disease.get("probability", 0.0))
        disease_name: str = top_disease.get("name", "Unknown Disease")
        disease_details: dict = top_disease.get("disease", {})
        severity = _severity_from_probability(probability)

        return DiseaseResponse(
            detected=True,
            disease=disease_name,
            confidence=int(probability * 100),
            severity=severity,
            affected_area=_affected_area_from_severity(severity),
            treatment=_build_treatment(disease_details),
        )

    except httpx.TimeoutException:
        logger.warning("Plant.id API request timed out — returning mock data")
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Plant.id API returned HTTP %s — returning mock data",
            exc.response.status_code,
        )
    except httpx.RequestError as exc:
        logger.warning("Plant.id API request failed (%s) — returning mock data", exc)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Unexpected error in disease detection (%s) — returning mock data", exc
        )

    return DiseaseResponse(is_mock=True, **_MOCK)
