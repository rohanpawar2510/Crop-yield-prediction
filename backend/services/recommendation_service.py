"""
recommendation_service.py — Farming recommendations via Gemini AI.

MODEL:    gemini-2.5-flash  (latest, free tier: 10 RPM, 500 RPD)
SDK:      google-genai  (pip install google-genai)
STRATEGY: response_schema (structured JSON output) — no truncation issues
FALLBACK: rule-based NPK gap analysis if Gemini fails / quota exceeded
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ─── NPK requirements per crop ────────────────────────────────────────────────

_CROP_NPK = {
    "SUGARCANE": {"n": 250, "p": 100, "k": 150},
    "WHEAT":     {"n": 120, "p": 60,  "k": 40},
    "RICE":      {"n": 120, "p": 60,  "k": 60},
    "COTTON":    {"n": 150, "p": 60,  "k": 60},
    "MAIZE":     {"n": 120, "p": 60,  "k": 40},
    "JOWAR":     {"n": 80,  "p": 40,  "k": 40},
    "BAJRA":     {"n": 80,  "p": 40,  "k": 40},
    "SOYABEAN":  {"n": 30,  "p": 60,  "k": 40},
    "GROUNDNUT": {"n": 25,  "p": 50,  "k": 50},
    "BANANA":    {"n": 200, "p": 60,  "k": 300},
    "POTATO":    {"n": 180, "p": 90,  "k": 200},
    "ONION":     {"n": 100, "p": 50,  "k": 100},
    "DEFAULT":   {"n": 120, "p": 60,  "k": 80},
}

# ─── Response schema (Gemini structured output) ───────────────────────────────

_RESPONSE_SCHEMA = {
    "type": "object",
    "required": [
        "soil_health_score", "soil_health_label",
        "npk_status", "primary_fertilizer", "secondary_fertilizer",
        "micronutrients", "application_schedule", "organic_alternatives",
        "warnings", "crop_rotation", "crop_rotation_reason",
        "expected_yield_boost", "irrigation_advice", "pest_risk", "general_tips"
    ],
    "properties": {
        "soil_health_score": {"type": "integer"},
        "soil_health_label": {"type": "string", "enum": ["Poor", "Fair", "Good", "Excellent"]},
        "crop_rotation":        {"type": "string"},
        "crop_rotation_reason": {"type": "string"},
        "irrigation_advice":    {"type": "string"},
        "pest_risk":            {"type": "string"},
        "expected_yield_boost": {"type": "string"},
        "general_tips":         {"type": "string"},
        "warnings": {"type": "array", "items": {"type": "string"}},

        "npk_status": {
            "type": "object",
            "required": ["nitrogen", "phosphorus", "potassium"],
            "properties": {
                "nitrogen":   {
                    "type": "object",
                    "required": ["current", "required", "status", "gap"],
                    "properties": {
                        "current":  {"type": "number"},
                        "required": {"type": "integer"},
                        "status":   {"type": "string"},
                        "gap":      {"type": "integer"}
                    }
                },
                "phosphorus": {
                    "type": "object",
                    "required": ["current", "required", "status", "gap"],
                    "properties": {
                        "current":  {"type": "number"},
                        "required": {"type": "integer"},
                        "status":   {"type": "string"},
                        "gap":      {"type": "integer"}
                    }
                },
                "potassium":  {
                    "type": "object",
                    "required": ["current", "required", "status", "gap"],
                    "properties": {
                        "current":  {"type": "number"},
                        "required": {"type": "integer"},
                        "status":   {"type": "string"},
                        "gap":      {"type": "integer"}
                    }
                },
            }
        },

        "primary_fertilizer": {
            "type": "object",
            "required": ["name", "grade", "quantity_per_ha", "total_quantity",
                         "estimated_cost_inr", "application_method"],
            "properties": {
                "name":               {"type": "string"},
                "grade":              {"type": "string"},
                "quantity_per_ha":    {"type": "string"},
                "total_quantity":     {"type": "string"},
                "estimated_cost_inr": {"type": "integer"},
                "application_method": {"type": "string"}
            }
        },

        "secondary_fertilizer": {
            "type": "object",
            "required": ["name", "grade", "quantity_per_ha", "total_quantity",
                         "estimated_cost_inr", "application_method"],
            "properties": {
                "name":               {"type": "string"},
                "grade":              {"type": "string"},
                "quantity_per_ha":    {"type": "string"},
                "total_quantity":     {"type": "string"},
                "estimated_cost_inr": {"type": "integer"},
                "application_method": {"type": "string"}
            }
        },

        "micronutrients": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "product", "dose", "reason"],
                "properties": {
                    "name":    {"type": "string"},
                    "product": {"type": "string"},
                    "dose":    {"type": "string"},
                    "reason":  {"type": "string"}
                }
            }
        },

        "application_schedule": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["stage", "timing", "fertilizers", "quantity"],
                "properties": {
                    "stage":       {"type": "string"},
                    "timing":      {"type": "string"},
                    "fertilizers": {"type": "string"},
                    "quantity":    {"type": "string"}
                }
            }
        },

        "organic_alternatives": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "quantity", "benefit"],
                "properties": {
                    "name":     {"type": "string"},
                    "quantity": {"type": "string"},
                    "benefit":  {"type": "string"}
                }
            }
        }
    }
}

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _npk_status(crop: str, n: float, p: float, k: float) -> dict:
    req = _CROP_NPK.get(crop.upper(), _CROP_NPK["DEFAULT"])

    def status(current, required):
        if current >= required * 1.1:
            return "Excess"
        elif current >= required * 0.85:
            return "Optimal"
        return "Deficient"

    return {
        "nitrogen":   {"current": n, "required": req["n"], "status": status(n, req["n"]), "gap": max(0, int(req["n"] - n))},
        "phosphorus": {"current": p, "required": req["p"], "status": status(p, req["p"]), "gap": max(0, int(req["p"] - p))},
        "potassium":  {"current": k, "required": req["k"], "status": status(k, req["k"]), "gap": max(0, int(req["k"] - k))},
    }


def _safe(v: Any, default: Any) -> Any:
    return v if v is not None else default

def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return default

def _safe_list(v: Any, default=None) -> list:
    return v if isinstance(v, list) else (default or [])

def _safe_dict(v: Any, default=None) -> dict:
    return v if isinstance(v, dict) else (default or {})


# ─── Fallback: rule-based ─────────────────────────────────────────────────────

def _fallback(crop: str, n: float, p: float, k: float, area: float) -> dict:
    req   = _CROP_NPK.get(crop.upper(), _CROP_NPK["DEFAULT"])
    n_gap = max(0, req["n"] - n)
    p_gap = max(0, req["p"] - p)
    k_gap = max(0, req["k"] - k)

    if n_gap >= p_gap and n_gap >= k_gap:
        qty_per_ha = int(n_gap / 0.46)
        primary = {
            "name": "Urea", "grade": "46-0-0",
            "quantity_per_ha":    f"{qty_per_ha} kg/ha",
            "total_quantity":     f"{qty_per_ha * area:,.0f} kg",
            "estimated_cost_inr": int(qty_per_ha * area * 20),
            "application_method": "Half at sowing, half at 30 DAS"
        }
    else:
        qty_per_ha = int(p_gap / 0.46)
        primary = {
            "name": "DAP", "grade": "18-46-0",
            "quantity_per_ha":    f"{qty_per_ha} kg/ha",
            "total_quantity":     f"{qty_per_ha * area:,.0f} kg",
            "estimated_cost_inr": int(qty_per_ha * area * 27),
            "application_method": "Full dose at sowing as band placement"
        }

    k_qty = int(k_gap / 0.60) if k_gap > 0 else 0
    secondary = {
        "name": "MOP", "grade": "0-0-60",
        "quantity_per_ha":    f"{k_qty} kg/ha" if k_qty else "Not required",
        "total_quantity":     f"{k_qty * area:,.0f} kg" if k_qty else "—",
        "estimated_cost_inr": int(k_qty * area * 15),
        "application_method": "Full dose at sowing"
    }

    return {
        "soil_health_score":    65,
        "soil_health_label":    "Fair",
        "npk_status":           _npk_status(crop, n, p, k),
        "primary_fertilizer":   primary,
        "secondary_fertilizer": secondary,
        "micronutrients": [
            {"name": "Zinc", "product": "Zinc Sulphate 21%",
             "dose": "25 kg/ha",
             "reason": "Commonly deficient in Maharashtra soils"}
        ],
        "application_schedule": [
            {"stage": "Pre-sowing",  "timing": "1 week before sowing", "fertilizers": "FYM",       "quantity": "5 t/ha"},
            {"stage": "Basal",       "timing": "At sowing",            "fertilizers": "DAP + MOP", "quantity": "Full P and K dose"},
            {"stage": "Top dress 1", "timing": "30 DAS",               "fertilizers": "Urea",      "quantity": "Half N dose"},
            {"stage": "Top dress 2", "timing": "60 DAS",               "fertilizers": "Urea",      "quantity": "Remaining N dose"},
        ],
        "organic_alternatives": [
            {"name": "Vermicompost",    "quantity": "2.5 t/ha", "benefit": "Improves soil biology and slow-release nutrients"},
            {"name": "Farmyard Manure", "quantity": "10 t/ha",  "benefit": "Improves soil structure and water retention"},
        ],
        "warnings": [
            "Gemini AI unavailable — showing rule-based NPK gap estimates",
            "Configure GEMINI_API_KEY for AI-powered recommendations",
        ],
        "crop_rotation":        "Legumes (Chickpea or Soybean)",
        "crop_rotation_reason": "Fixes nitrogen, breaks pest cycles",
        "expected_yield_boost": "10–15%",
        "irrigation_advice":    "Maintain 60–70% soil moisture at critical growth stages",
        "pest_risk":            "Monitor regularly — contact local Krishi Sevak for advice",
        "general_tips":         "Test soil annually. Maintain pH 6.5–7.5 for optimal nutrient uptake.",
    }


# ─── Gemini call ──────────────────────────────────────────────────────────────

def _call_gemini(
    crop: str, location: str, season: str, soil_type: str,
    irrigation_type: str, area: float,
    n: float, p: float, k: float,
    ph: float, temperature: float, rainfall: float,
    predicted_yield: float,
) -> dict:
    from google import genai
    from google.genai import types

    # Import here to avoid circular imports at module load time
    import config
    client = genai.Client(api_key=config.GEMINI_API_KEY)

    prompt = f"""You are an expert agricultural scientist for Maharashtra, India.
Provide fertilizer and farming recommendations for this farmer.

Crop: {crop}
Location: {location}, Maharashtra
Season: {season}
Soil type: {soil_type}
Irrigation: {irrigation_type}
Farm area: {area} ha
Nitrogen: {n} kg/ha (current soil level)
Phosphorus: {p} kg/ha (current soil level)
Potassium: {k} kg/ha (current soil level)
pH: {ph}
Temperature: {temperature}°C
Annual rainfall: {rainfall} mm
Expected yield: {predicted_yield:.2f} tons/ha

Instructions:
- Return ONLY valid JSON.
- Never truncate output.
- Keep all text fields under 50 characters.
- warnings maximum 2 items.
- micronutrients maximum 2 items.
- application_schedule maximum 3 items.
- organic_alternatives maximum 2 items.
- Give specific practical advice for Maharashtra farmers.
- total_quantity = quantity_per_ha × area.
- Fertilizer prices:
  Urea ₹20/kg
  DAP ₹27/kg
  MOP ₹15/kg
  SSP ₹13/kg
- NPK status must reflect actual soil values."""

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=4096,
            response_mime_type="application/json",
            response_schema=_RESPONSE_SCHEMA,
        ),
    )
    print("\n========================")
    print("GEMINI RESPONSE")
    print("========================")
    print(response.text)
    print("========================\n")

    return json.loads(response.text)

    


# ─── Public API ───────────────────────────────────────────────────────────────

def get_recommendations(
    location:        str,
    nitrogen:        float,
    phosphorus:      float,
    potassium:       float,
    ph:              float,
    crop:            str   = "Unknown",
    season:          str   = "Kharif",
    soil_type:       str   = "Black",
    irrigation_type: str   = "Rainfed",
    area:            float = 1.0,
    temperature:     float = 25.0,
    rainfall:        float = 800.0,
    predicted_yield: float = 0.0,
) -> dict:
    """
    Returns recommendation dict.
    Tries Gemini 2.5 Flash with structured output (response_schema).
    Falls back to rule-based NPK analysis on any failure.
    """
    import config

    if not getattr(config, "GEMINI_API_KEY", None):
        logger.warning("No GEMINI_API_KEY set — using fallback")
        return _fallback(crop, nitrogen, phosphorus, potassium, area)

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Gemini attempt %d/%d — crop=%s location=%s",
                        attempt, max_retries, crop, location)

            data = _call_gemini(
                crop=crop, location=location, season=season,
                soil_type=soil_type, irrigation_type=irrigation_type,
                area=area, n=nitrogen, p=phosphorus, k=potassium,
                ph=ph, temperature=temperature, rainfall=rainfall,
                predicted_yield=predicted_yield,
            )

            logger.info("✅ Gemini structured output OK — crop=%s", crop)

            # Ensure npk_status is always populated (fallback to computed)
            if not _safe_dict(data.get("npk_status")):
                data["npk_status"] = _npk_status(crop, nitrogen, phosphorus, potassium)

            return {
                "soil_health_score":    _safe_int(data.get("soil_health_score"), 70),
                "soil_health_label":    _safe(data.get("soil_health_label"), "Good"),
                "npk_status":           _safe_dict(data.get("npk_status"),
                                            _npk_status(crop, nitrogen, phosphorus, potassium)),
                "primary_fertilizer":   _safe_dict(data.get("primary_fertilizer"), {}),
                "secondary_fertilizer": _safe_dict(data.get("secondary_fertilizer"), {}),
                "micronutrients":       _safe_list(data.get("micronutrients"), []),
                "application_schedule": _safe_list(data.get("application_schedule"), []),
                "organic_alternatives": _safe_list(data.get("organic_alternatives"), []),
                "warnings":             _safe_list(data.get("warnings"), []),
                "crop_rotation":        _safe(data.get("crop_rotation"), ""),
                "crop_rotation_reason": _safe(data.get("crop_rotation_reason"), ""),
                "expected_yield_boost": _safe(data.get("expected_yield_boost"), ""),
                "irrigation_advice":    _safe(data.get("irrigation_advice"), ""),
                "pest_risk":            _safe(data.get("pest_risk"), ""),
                "general_tips":         _safe(data.get("general_tips"), ""),
            }

        except Exception as exc:
            err = str(exc)

            # Quota exceeded — wait and retry
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                wait = 60 * attempt  # 60s, 120s, 180s
                logger.warning("Gemini 429 (attempt %d/%d) — waiting %ds", attempt, max_retries, wait)
                time.sleep(wait)
                continue

            # Model not found — no point retrying
            if "404" in err or "NOT_FOUND" in err:
                logger.error("Gemini model not found — check model name in config")
                break

            # Other errors — short wait, retry
            logger.warning("Gemini error (attempt %d/%d): %s", attempt, max_retries, exc)
            if attempt < max_retries:
                time.sleep(2)
                continue
            break

    logger.warning("All Gemini attempts failed — using rule-based fallback")
    return _fallback(crop, nitrogen, phosphorus, potassium, area)