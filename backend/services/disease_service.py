"""
disease_service.py — Plant disease detection using Plant.id API v2.

Plant name fix:
  - health_assessment endpoint often returns empty suggestions[]
  - Solution: separate call to /v2/identify to reliably get plant name
  - _safe_str() handles treatment fields returned as list or string
"""

from __future__ import annotations

import base64
import logging
import mimetypes
from typing import Union

import httpx

import config
from models.schemas import DiseaseResponse

logger = logging.getLogger(__name__)

_API_TIMEOUT:     int = 30
_IDENTIFY_TIMEOUT: int = 15

_ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)

# Plant.id endpoints
_HEALTH_URL   = "https://api.plant.id/v2/health_assessment"
_IDENTIFY_URL = "https://api.plant.id/v2/identify"

# ─── Mock fallback ────────────────────────────────────────────────────────────

_MOCK = DiseaseResponse(
    detected=True,
    disease="Leaf Blight (Mock Data)",
    confidence=87,
    severity="Moderate",
    affected_area="30-50%",
    treatment="Apply Mancozeb 75WP @ 2g/L water. Spray every 7-10 days.",
    is_mock=True,
    plant_name="Unknown Plant (Mock)",
    is_healthy=False,
    all_diseases=[
        {"name": "Leaf Blight",    "probability": 87.0, "common_names": ["Blight"]},
        {"name": "Bacterial Spot", "probability": 8.0,  "common_names": ["Spot disease"]},
        {"name": "Healthy",        "probability": 5.0,  "common_names": []},
    ],
    prevention="Avoid overhead irrigation. Maintain proper plant spacing.",
    biological_treatment="Apply Trichoderma viride 2.5 kg/ha",
    chemical_treatment="Mancozeb 75WP @ 2g/L or Copper Oxychloride 3g/L",
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _safe_str(value: Union[str, list, None], default: str = "") -> str:
    """Handle Plant.id treatment fields which can be str, list, or None."""
    if value is None:            return default
    if isinstance(value, str):   return value.strip()
    if isinstance(value, list):  return " ".join(str(i).strip() for i in value if i)
    return str(value).strip() or default


def _get_mime_type(filename: str, image_bytes: bytes) -> str:
    if filename:
        mime, _ = mimetypes.guess_type(filename)
        if mime and mime in _ALLOWED_MIME_TYPES:
            return mime
    if image_bytes[:3] == b"\xff\xd8\xff":          return "image/jpeg"
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":     return "image/png"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP": return "image/webp"
    return "image/jpeg"


def _severity_from_probability(p: float) -> str:
    if p >= 0.80: return "Severe"
    if p >= 0.60: return "Moderate"
    if p >= 0.40: return "Mild"
    return "Suspected"


def _affected_area_from_probability(p: float) -> str:
    if p >= 0.80: return "60-80%"
    if p >= 0.60: return "30-60%"
    if p >= 0.40: return "10-30%"
    return "< 10%"


def _extract_treatment(disease_details: dict) -> tuple[str, str, str, str]:
    """Extract treatment — handles list or string values from Plant.id."""
    treatment_obj = disease_details.get("treatment", {})
    chemical   = _safe_str(treatment_obj.get("chemical"),   "Consult local agronomist")
    biological = _safe_str(treatment_obj.get("biological"), "")
    prevention = _safe_str(treatment_obj.get("prevention"), "")
    parts = []
    if chemical:   parts.append(f"Chemical: {chemical}")
    if biological: parts.append(f"Biological: {biological}")
    if prevention: parts.append(f"Prevention: {prevention}")
    full = " | ".join(parts) if parts else "Consult local agronomist"
    return full, chemical, biological, prevention


# ─── KEY FIX: Separate plant identification call ──────────────────────────────

def _identify_plant(image_b64: str, mime_type: str) -> str:
    """
    Call /v2/identify to get plant common name.

    Why separate call:
      /v2/health_assessment focuses on disease detection.
      Its suggestions[] field is often empty for unclear images.
      /v2/identify is specifically designed for plant identification
      and reliably returns common names.
    """
    try:
        response = httpx.post(
            _IDENTIFY_URL,
            headers={
                "Api-Key":       config.PLANT_ID_API_KEY,
                "Content-Type":  "application/json",
            },
            json={
                "images":         [f"data:{mime_type};base64,{image_b64}"],
                "plant_details":  ["common_names"],
                "plant_language": "en",
            },
            timeout=_IDENTIFY_TIMEOUT,
        )

        if response.status_code != 200:
            logger.warning("Plant identify returned %d", response.status_code)
            return "Unknown Plant"

        data        = response.json()
        suggestions = data.get("suggestions", [])

        if not suggestions:
            logger.warning("Plant identify returned no suggestions")
            return "Unknown Plant"

        top           = suggestions[0]
        probability   = float(top.get("probability", 0))
        plant_details = top.get("plant_details", {})
        common_names  = plant_details.get("common_names", [])

        logger.info(
            "Plant identified: %s (%.0f%%) common_names=%s",
            top.get("plant_name"), probability * 100, common_names,
        )

        # Prefer common name over scientific name
        if common_names and isinstance(common_names, list):
            return common_names[0]   # e.g. "Rice"

        # Fallback to scientific name
        sci = top.get("plant_name", "")
        return sci if sci else "Unknown Plant"

    except Exception as exc:
        logger.warning("Plant identify call failed: %s", exc)
        return "Unknown Plant"


# ─── Main detection function ──────────────────────────────────────────────────

def detect_disease(image_bytes: bytes, filename: str) -> DiseaseResponse:
    """
    Detect plant disease using Plant.id API v2.

    Step 1: Call /v2/identify   → get plant common name
    Step 2: Call /v2/health_assessment → get disease info
    Falls back to mock on any error.
    """
    if not image_bytes:
        return _MOCK

    mime_type = _get_mime_type(filename, image_bytes)
    if mime_type not in _ALLOWED_MIME_TYPES:
        return DiseaseResponse(
            detected=False,
            disease="Invalid image format",
            confidence=0,
            severity="Error",
            affected_area="N/A",
            treatment="Please upload JPEG, PNG or WebP image",
            is_mock=True,
            plant_name="", is_healthy=False, all_diseases=[],
            prevention="", biological_treatment="", chemical_treatment="",
        )

    if not config.PLANT_ID_API_KEY:
        logger.warning("PLANT_ID_API_KEY not set — returning mock")
        return _MOCK

    # ── Encode image once, reuse for both calls ────────────────────────────────
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    data_uri  = f"data:{mime_type};base64,{b64_image}"

    # ── Step 1: Identify plant (separate call) ────────────────────────────────
    plant_name = _identify_plant(b64_image, mime_type)
    logger.info("Plant name resolved: %s", plant_name)

    # ── Step 2: Disease detection ─────────────────────────────────────────────
    payload = {
        "images":          [data_uri],
        "modifiers":       ["similar_images"],
        "plant_language":  "en",
        "disease_details": [
            "cause", "common_names", "classification",
            "description", "treatment", "url",
        ],
        "plant_details":   ["common_names"],
    }

    headers = {
        "Content-Type": "application/json",
        "Api-Key":       config.PLANT_ID_API_KEY,
    }

    try:
        response = httpx.post(
            _HEALTH_URL,
            json=payload,
            headers=headers,
            timeout=_API_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        # ── Health assessment ─────────────────────────────────────────────────
        health       = data.get("health_assessment", {})
        is_healthy   = health.get("is_healthy", True)
        healthy_prob = float(health.get("is_healthy_probability", 1.0))
        diseases     = health.get("diseases", [])

        logger.info(
            "Disease detection → plant=%s is_healthy=%s diseases=%d",
            plant_name, is_healthy, len(diseases),
        )

        # ── Healthy plant ─────────────────────────────────────────────────────
        if is_healthy or not diseases:
            return DiseaseResponse(
                detected=False,
                disease="No disease detected",
                confidence=int(healthy_prob * 100),
                severity="None",
                affected_area="0%",
                treatment="Plant appears healthy. Continue regular monitoring.",
                is_mock=False,
                plant_name=plant_name,
                is_healthy=True,
                all_diseases=[],
                prevention="Maintain good agricultural practices",
                biological_treatment="None required",
                chemical_treatment="None required",
            )

        # ── Top disease ───────────────────────────────────────────────────────
        top          = diseases[0]
        probability  = float(top.get("probability", 0.0))
        disease_name = top.get("name", "Unknown Disease")

        # disease_details key (v2) or disease key (v3)
        disease_details = top.get("disease_details", top.get("disease", {}))
        full_tx, chemical, biological, prevention = _extract_treatment(disease_details)

        # ── All diseases top 5 ────────────────────────────────────────────────
        all_diseases = []
        for d in diseases[:5]:
            dd = d.get("disease_details", d.get("disease", {}))
            all_diseases.append({
                "name":         d.get("name", "Unknown"),
                "probability":  round(float(d.get("probability", 0)) * 100, 1),
                "common_names": dd.get("common_names", []),
            })

        logger.info(
            "✅ Result → plant=%s disease=%s confidence=%.0f%%",
            plant_name, disease_name, probability * 100,
        )

        return DiseaseResponse(
            detected=True,
            disease=disease_name,
            confidence=int(probability * 100),
            severity=_severity_from_probability(probability),
            affected_area=_affected_area_from_probability(probability),
            treatment=full_tx,
            is_mock=False,
            plant_name=plant_name,
            is_healthy=False,
            all_diseases=all_diseases,
            prevention=prevention,
            biological_treatment=biological,
            chemical_treatment=chemical,
        )

    except httpx.TimeoutException:
        logger.warning("Plant.id health_assessment timeout — returning mock")
    except httpx.HTTPStatusError as exc:
        logger.warning("Plant.id HTTP %s — returning mock", exc.response.status_code)
        if exc.response.status_code == 403:
            logger.error("❌ Plant.id API key INVALID or EXPIRED")
        elif exc.response.status_code == 429:
            logger.error("⚠️ Plant.id rate limit exceeded")
    except httpx.RequestError as exc:
        logger.warning("Plant.id request failed: %s", exc)
    except Exception as exc:
        logger.warning("Plant.id unexpected error: %s", exc)

    return _MOCK