"""
recommendation_service.py — Smart farming recommendations powered by Gemini AI.

Uses Google Gemini AI to generate personalized farming recommendations based on
soil and environmental data.  Falls back to mock data on any error.
"""

from __future__ import annotations

import json
import logging
import re

import config
from models.schemas import FertilizerDetail, RecommendResponse

logger = logging.getLogger(__name__)

# ─── Mock fallback ────────────────────────────────────────────────────────────

_MOCK_FERTILIZER = FertilizerDetail(
    primary="NPK 20-10-10",
    amount="150 kg/hectare",
    schedule="Apply at sowing and 30 days after germination",
    alternatives=["Urea + DAP", "Organic compost (5 ton/ha)"],
    distribution={"nitrogen": 40, "phosphorus": 25, "potassium": 20, "organic": 15},
)

_MOCK_RESPONSE = RecommendResponse(
    fertilizer=_MOCK_FERTILIZER,
    crop_rotation=(
        "Follow Rice with Legumes (e.g., Lentils or Chickpeas) in the next season "
        "to restore soil nitrogen."
    ),
    irrigation="Maintain soil moisture at 60-70%. Irrigate every 5-7 days during dry spells.",
    pest_management=(
        "Monitor for stem borers and leaf folders. Use neem-based sprays "
        "as part of integrated pest management."
    ),
    general=(
        "Based on the soil pH and nutrient levels, the conditions are suitable for "
        "a range of crops. Consider liming if pH drops below 6.0."
    ),
)

# ─── Prompt template ─────────────────────────────────────────────────────────

_PROMPT_TEMPLATE = """You are an expert agricultural scientist and farming advisor. Based on the following soil and environmental data, provide detailed farming recommendations.

Soil Data:
- Nitrogen (N): {nitrogen} kg/ha
- Phosphorus (P): {phosphorus} kg/ha
- Potassium (K): {potassium} kg/ha
- pH Level: {ph}

Location: {location}

Provide recommendations in the following JSON format ONLY (no extra text):
{{
  "fertilizer": {{
    "primary": "Name of primary fertilizer (e.g., NPK 20-10-10)",
    "amount": "Amount in kg/hectare (e.g., 150 kg/hectare)",
    "schedule": "When to apply (e.g., Apply at sowing and 30 days after germination)",
    "alternatives": ["Alternative 1", "Alternative 2"],
    "distribution": {{
      "nitrogen": 40,
      "phosphorus": 25,
      "potassium": 20,
      "organic": 15
    }}
  }},
  "crop_rotation": "Suggested crop rotation plan",
  "irrigation": "Irrigation advice based on conditions",
  "pest_management": "Pest prevention and management tips",
  "general": "General farming advice for these conditions"
}}"""


# ─── Gemini helper ────────────────────────────────────────────────────────────

def _call_gemini(prompt: str) -> dict:
    """Call the Gemini API and return the parsed JSON response.

    Raises:
        Exception: on any API, timeout, or parsing error.
    """
    import google.generativeai as genai  # lazy import — optional dependency

    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel(config.GEMINI_MODEL)

    generation_config = genai.types.GenerationConfig(
        temperature=0.4,
        candidate_count=1,
    )

    response = model.generate_content(
        prompt,
        generation_config=generation_config,
        request_options={"timeout": 15},
    )

    raw_text: str = response.text

    # Strip optional markdown code fences (```json ... ```)
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    return json.loads(cleaned)


# ─── Public API ───────────────────────────────────────────────────────────────

def get_recommendations(
    location: str,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph: float,
) -> RecommendResponse:
    """Return smart farming recommendations for the given inputs.

    Calls Google Gemini AI to generate personalized advice.  Falls back to
    mock data if the API key is missing, the request fails, or the response
    cannot be parsed as JSON.

    Args:
        location: City or region name.
        nitrogen: Nitrogen content in kg/ha.
        phosphorus: Phosphorus content in kg/ha.
        potassium: Potassium content in kg/ha.
        ph: Soil pH value (0–14).

    Returns:
        RecommendResponse with AI-generated or mock recommendations.
    """
    if not config.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY is not set — returning mock recommendations.")
        return _MOCK_RESPONSE

    prompt = _PROMPT_TEMPLATE.format(
        nitrogen=nitrogen,
        phosphorus=phosphorus,
        potassium=potassium,
        ph=ph,
        location=location,
    )

    try:
        data = _call_gemini(prompt)

        fertilizer_data = data["fertilizer"]
        fertilizer = FertilizerDetail(
            primary=fertilizer_data["primary"],
            amount=fertilizer_data["amount"],
            schedule=fertilizer_data["schedule"],
            alternatives=fertilizer_data["alternatives"],
            distribution=fertilizer_data["distribution"],
        )

        return RecommendResponse(
            fertilizer=fertilizer,
            crop_rotation=data["crop_rotation"],
            irrigation=data["irrigation"],
            pest_management=data["pest_management"],
            general=data["general"],
        )

    except json.JSONDecodeError as exc:
        logger.warning("Gemini returned invalid JSON — falling back to mock data. Error: %s", exc)
        return _MOCK_RESPONSE
    except KeyError as exc:
        logger.warning("Gemini response missing expected field %s — falling back to mock data.", exc)
        return _MOCK_RESPONSE
    except Exception as exc:  # noqa: BLE001
        logger.warning("Gemini API call failed — falling back to mock data. Error: %s", exc)
        return _MOCK_RESPONSE
