"""
test_recommendation_service.py — Test cases for recommendation_service.py
=========================================================================
Tests cover:
  - NPK status calculation (_npk_status)
  - Fallback rule-based recommendations (_fallback)
  - get_recommendations() with Gemini mocked
  - get_recommendations() fallback when no API key
  - Response structure validation
  - All 12 crops in _CROP_NPK

Run:
    pytest tests/test_recommendation_service.py -v
    pytest tests/test_recommendation_service.py -v -k "npk"
    pytest tests/test_recommendation_service.py -v -k "fallback"
    pytest tests/test_recommendation_service.py -v -k "gemini"
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# ── Mock config before import ─────────────────────────────────────────────────
import types
config_mock = types.ModuleType("config")
config_mock.GEMINI_API_KEY = "fake-test-key"
config_mock.GEMINI_MODEL   = "gemini-2.5-flash"
sys.modules["config"] = config_mock

from services.recommendation_service import (
    get_recommendations,
    _npk_status,
    _fallback,
    _CROP_NPK,
)

# ── Shared mock Gemini response ───────────────────────────────────────────────
MOCK_GEMINI_RESPONSE = {
    "soil_health_score":    72,
    "soil_health_label":    "Good",
    "npk_status": {
        "nitrogen":   {"current": 65.0, "required": 250, "status": "Deficient", "gap": 185},
        "phosphorus": {"current": 75.0, "required": 100, "status": "Deficient", "gap": 25},
        "potassium":  {"current": 110.0,"required": 150, "status": "Deficient", "gap": 40},
    },
    "primary_fertilizer": {
        "name": "Urea", "grade": "46-0-0",
        "quantity_per_ha": "400 kg", "total_quantity": "1600 kg",
        "estimated_cost_inr": 32000, "application_method": "Split in 3 doses"
    },
    "secondary_fertilizer": {
        "name": "DAP", "grade": "18-46-0",
        "quantity_per_ha": "100 kg", "total_quantity": "400 kg",
        "estimated_cost_inr": 10800, "application_method": "Basal at sowing"
    },
    "micronutrients": [
        {"name": "Zinc", "product": "Zinc Sulphate", "dose": "25 kg/ha", "reason": "Prevents chlorosis"}
    ],
    "application_schedule": [
        {"stage": "Basal",    "timing": "At sowing",  "fertilizers": "DAP",  "quantity": "100 kg"},
        {"stage": "Tillering","timing": "60 DAS",      "fertilizers": "Urea", "quantity": "200 kg"},
    ],
    "organic_alternatives": [
        {"name": "FYM", "quantity": "10 t/ha", "benefit": "Improves soil structure"}
    ],
    "warnings":             ["Rainfed sugarcane is risky"],
    "crop_rotation":        "Soybean",
    "crop_rotation_reason": "Fixes nitrogen",
    "expected_yield_boost": "20%",
    "irrigation_advice":    "Use drip irrigation",
    "pest_risk":            "Medium — watch for stem borer",
    "general_tips":         "Test soil annually",
}

# ── Base input ────────────────────────────────────────────────────────────────
BASE_INPUT = dict(
    location="Pune", crop="SUGARCANE", season="Kharif",
    soil_type="Black", irrigation_type="Rainfed",
    area=4.0, nitrogen=65.0, phosphorus=75.0, potassium=110.0,
    ph=7.0, temperature=28.0, rainfall=800.0, predicted_yield=8.0,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. NPK STATUS TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestNPKStatus:

    def test_sugarcane_nitrogen_deficient(self):
        """Sugarcane needs 250 N — 65 should be Deficient."""
        result = _npk_status("SUGARCANE", n=65, p=75, k=110)
        assert result["nitrogen"]["status"] == "Deficient"
        assert result["nitrogen"]["current"] == 65
        assert result["nitrogen"]["required"] == 250
        assert result["nitrogen"]["gap"] == 185

    def test_sugarcane_potassium_deficient(self):
        """Sugarcane needs 150 K — 110 should be Deficient."""
        result = _npk_status("SUGARCANE", n=65, p=75, k=110)
        assert result["potassium"]["status"] == "Deficient"
        assert result["potassium"]["gap"] == 40

    def test_wheat_nitrogen_optimal(self):
        """Wheat needs 120 N — 110 is within 85% threshold → Optimal."""
        result = _npk_status("WHEAT", n=110, p=60, k=40)
        assert result["nitrogen"]["status"] == "Optimal"
        assert result["nitrogen"]["gap"] == 0

    def test_excess_nitrogen(self):
        """N > 110% of required → Excess."""
        result = _npk_status("WHEAT", n=140, p=60, k=40)
        assert result["nitrogen"]["status"] == "Excess"
        assert result["nitrogen"]["gap"] == 0

    def test_optimal_phosphorus(self):
        """P exactly at required → Optimal."""
        result = _npk_status("WHEAT", n=80, p=60, k=40)
        assert result["phosphorus"]["status"] == "Optimal"

    def test_gap_is_zero_when_optimal(self):
        """Gap must be 0 when nutrient is Optimal or Excess."""
        result = _npk_status("WHEAT", n=120, p=60, k=40)
        assert result["nitrogen"]["gap"] == 0
        assert result["phosphorus"]["gap"] == 0
        assert result["potassium"]["gap"] == 0

    def test_gap_is_non_negative(self):
        """Gap must never be negative."""
        result = _npk_status("SUGARCANE", n=300, p=150, k=200)
        assert result["nitrogen"]["gap"]   >= 0
        assert result["phosphorus"]["gap"] >= 0
        assert result["potassium"]["gap"]  >= 0

    def test_unknown_crop_uses_default(self):
        """Unknown crop should use DEFAULT NPK values."""
        result = _npk_status("MANGO", n=80, p=40, k=50)
        assert result["nitrogen"]["required"]   == _CROP_NPK["DEFAULT"]["n"]
        assert result["phosphorus"]["required"] == _CROP_NPK["DEFAULT"]["p"]
        assert result["potassium"]["required"]  == _CROP_NPK["DEFAULT"]["k"]

    def test_case_insensitive(self):
        """Crop name should work regardless of case."""
        upper = _npk_status("SUGARCANE", n=65, p=75, k=110)
        lower = _npk_status("sugarcane", n=65, p=75, k=110)
        assert upper["nitrogen"]["required"] == lower["nitrogen"]["required"]

    def test_all_crops_have_npk_requirements(self):
        """Every crop in _CROP_NPK should return correct required values."""
        for crop, req in _CROP_NPK.items():
            if crop == "DEFAULT":
                continue
            result = _npk_status(crop, n=0, p=0, k=0)
            assert result["nitrogen"]["required"]   == req["n"], f"{crop} N wrong"
            assert result["phosphorus"]["required"] == req["p"], f"{crop} P wrong"
            assert result["potassium"]["required"]  == req["k"], f"{crop} K wrong"

    def test_npk_structure_has_all_keys(self):
        """NPK status must always return all required keys."""
        result = _npk_status("WHEAT", n=80, p=40, k=30)
        for nutrient in ["nitrogen", "phosphorus", "potassium"]:
            assert nutrient in result
            for key in ["current", "required", "status", "gap"]:
                assert key in result[nutrient], f"Missing {key} in {nutrient}"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. FALLBACK TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestFallback:

    def test_fallback_returns_dict(self):
        """Fallback must return a dict."""
        result = _fallback("SUGARCANE", n=65, p=75, k=110, area=4.0)
        assert isinstance(result, dict)

    def test_fallback_has_all_required_fields(self):
        """Fallback must have all required fields."""
        result = _fallback("WHEAT", n=80, p=40, k=30, area=2.0)
        required = [
            "soil_health_score", "soil_health_label", "npk_status",
            "primary_fertilizer", "secondary_fertilizer", "micronutrients",
            "application_schedule", "organic_alternatives", "warnings",
            "crop_rotation", "crop_rotation_reason", "expected_yield_boost",
            "irrigation_advice", "pest_risk", "general_tips",
        ]
        for field in required:
            assert field in result, f"Missing field: {field}"

    def test_fallback_soil_score_is_65(self):
        """Fallback always returns soil_health_score = 65."""
        result = _fallback("WHEAT", n=80, p=40, k=30, area=2.0)
        assert result["soil_health_score"] == 65

    def test_fallback_soil_label_is_fair(self):
        """Fallback always returns soil_health_label = Fair."""
        result = _fallback("WHEAT", n=80, p=40, k=30, area=2.0)
        assert result["soil_health_label"] == "Fair"

    def test_fallback_primary_fertilizer_urea_when_n_deficient(self):
        """When N gap is largest, primary fertilizer should be Urea."""
        # Sugarcane N gap = 250-65 = 185 (largest)
        result = _fallback("SUGARCANE", n=65, p=90, k=140, area=4.0)
        assert result["primary_fertilizer"]["name"] == "Urea"
        assert result["primary_fertilizer"]["grade"] == "46-0-0"

    def test_fallback_primary_fertilizer_dap_when_p_deficient(self):
        """When P gap is largest, primary fertilizer should be DAP."""
        # Make P gap largest: crop with high P need, low N need
        result = _fallback("SOYABEAN", n=25, p=10, k=35, area=2.0)
        # Soyabean: N=30, P=60, K=40 → P gap=50, N gap=5, K gap=5
        assert result["primary_fertilizer"]["name"] == "DAP"

    def test_fallback_cost_scales_with_area(self):
        """Cost should be proportional to area."""
        result1 = _fallback("WHEAT", n=50, p=20, k=10, area=1.0)
        result2 = _fallback("WHEAT", n=50, p=20, k=10, area=2.0)
        cost1 = result1["primary_fertilizer"]["estimated_cost_inr"]
        cost2 = result2["primary_fertilizer"]["estimated_cost_inr"]
        assert cost2 == cost1 * 2

    def test_fallback_warnings_mention_gemini(self):
        """Fallback warnings should mention Gemini unavailable."""
        result = _fallback("WHEAT", n=80, p=40, k=30, area=2.0)
        warnings_text = " ".join(result["warnings"]).lower()
        assert "gemini" in warnings_text

    def test_fallback_application_schedule_not_empty(self):
        """Fallback should always have application schedule."""
        result = _fallback("RICE", n=80, p=40, k=40, area=3.0)
        assert len(result["application_schedule"]) > 0

    def test_fallback_micronutrients_has_zinc(self):
        """Fallback micronutrients should always include Zinc."""
        result = _fallback("COTTON", n=100, p=40, k=40, area=5.0)
        names = [m["name"] for m in result["micronutrients"]]
        assert "Zinc" in names

    def test_fallback_npk_status_correct(self):
        """Fallback NPK status must use our calculated values, not Gemini."""
        result = _fallback("SUGARCANE", n=65, p=75, k=110, area=4.0)
        npk = result["npk_status"]
        assert npk["nitrogen"]["current"]  == 65
        assert npk["nitrogen"]["required"] == 250
        assert npk["nitrogen"]["status"]   == "Deficient"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. GET_RECOMMENDATIONS WITH GEMINI MOCKED
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetRecommendationsGemini:

    def _mock_call(self, return_value=None):
        """Helper to patch _call_gemini."""
        return patch(
            "services.recommendation_service._call_gemini",
            return_value=return_value or MOCK_GEMINI_RESPONSE
        )

    def test_returns_dict(self):
        """get_recommendations must return a dict."""
        with self._mock_call():
            result = get_recommendations(**BASE_INPUT)
        assert isinstance(result, dict)

    def test_has_all_required_fields(self):
        """Response must have all required fields."""
        with self._mock_call():
            result = get_recommendations(**BASE_INPUT)
        required = [
            "soil_health_score", "soil_health_label", "npk_status",
            "primary_fertilizer", "secondary_fertilizer", "micronutrients",
            "application_schedule", "organic_alternatives", "warnings",
            "crop_rotation", "crop_rotation_reason", "expected_yield_boost",
            "irrigation_advice", "pest_risk", "general_tips",
        ]
        for field in required:
            assert field in result, f"Missing: {field}"

    def test_soil_health_score_from_gemini(self):
        """Soil health score should come from Gemini response."""
        with self._mock_call():
            result = get_recommendations(**BASE_INPUT)
        assert result["soil_health_score"] == 72

    def test_soil_health_label_valid(self):
        """Soil health label must be one of the valid enum values."""
        with self._mock_call():
            result = get_recommendations(**BASE_INPUT)
        assert result["soil_health_label"] in ["Poor", "Fair", "Good", "Excellent"]

    def test_npk_status_overridden_with_calculated(self):
        """NPK status must use our _npk_status(), not Gemini's values."""
        with self._mock_call():
            result = get_recommendations(**BASE_INPUT)
        # Our calculation: SUGARCANE needs N=250, current=65 → Deficient
        assert result["npk_status"]["nitrogen"]["required"] == 250
        assert result["npk_status"]["nitrogen"]["status"]   == "Deficient"

    def test_primary_fertilizer_has_name(self):
        """Primary fertilizer must have a name."""
        with self._mock_call():
            result = get_recommendations(**BASE_INPUT)
        assert result["primary_fertilizer"]["name"] != ""

    def test_primary_fertilizer_cost_positive(self):
        """Fertilizer cost must be positive."""
        with self._mock_call():
            result = get_recommendations(**BASE_INPUT)
        assert result["primary_fertilizer"]["estimated_cost_inr"] > 0

    def test_application_schedule_is_list(self):
        """Application schedule must be a list."""
        with self._mock_call():
            result = get_recommendations(**BASE_INPUT)
        assert isinstance(result["application_schedule"], list)

    def test_micronutrients_is_list(self):
        """Micronutrients must be a list."""
        with self._mock_call():
            result = get_recommendations(**BASE_INPUT)
        assert isinstance(result["micronutrients"], list)

    def test_warnings_is_list(self):
        """Warnings must be a list."""
        with self._mock_call():
            result = get_recommendations(**BASE_INPUT)
        assert isinstance(result["warnings"], list)

    def test_crop_rotation_is_string(self):
        """Crop rotation must be a non-empty string."""
        with self._mock_call():
            result = get_recommendations(**BASE_INPUT)
        assert isinstance(result["crop_rotation"], str)
        assert len(result["crop_rotation"]) > 0

    def test_different_crops_get_recommendations(self):
        """All supported crops should get recommendations."""
        crops = ["WHEAT", "RICE", "COTTON", "MAIZE", "JOWAR",
                 "BAJRA", "SOYABEAN", "GROUNDNUT", "BANANA",
                 "POTATO", "ONION", "SUGARCANE"]
        for crop in crops:
            with self._mock_call():
                result = get_recommendations(**{**BASE_INPUT, "crop": crop})
            assert "soil_health_score" in result, f"Failed for crop: {crop}"

    def test_different_locations(self):
        """Different Maharashtra locations should all work."""
        locations = ["Pune", "Nagpur", "Nashik", "Aurangabad", "Kolhapur"]
        for loc in locations:
            with self._mock_call():
                result = get_recommendations(**{**BASE_INPUT, "location": loc})
            assert "soil_health_score" in result, f"Failed for location: {loc}"

    def test_different_seasons(self):
        """All seasons should work."""
        for season in ["Kharif", "Rabi", "Zaid", "Annual"]:
            with self._mock_call():
                result = get_recommendations(**{**BASE_INPUT, "season": season})
            assert "soil_health_score" in result, f"Failed for season: {season}"

    def test_gemini_failure_falls_back(self):
        """When Gemini raises exception, fallback should be used."""
        with patch("services.recommendation_service._call_gemini",
                   side_effect=Exception("Gemini connection error")):
            result = get_recommendations(**BASE_INPUT)
        assert "soil_health_score" in result
        # Fallback always returns 65
        assert result["soil_health_score"] == 65
        warnings_text = " ".join(result["warnings"]).lower()
        assert "gemini" in warnings_text

    def test_gemini_404_falls_back(self):
        """When model not found (404), fallback should be used."""
        with patch("services.recommendation_service._call_gemini",
                   side_effect=Exception("404 NOT_FOUND model does not exist")):
            result = get_recommendations(**BASE_INPUT)
        assert result["soil_health_score"] == 65

    def test_no_api_key_uses_fallback(self):
        """No API key should immediately return fallback."""
        import services.recommendation_service as svc
        original = config_mock.GEMINI_API_KEY
        config_mock.GEMINI_API_KEY = ""
        try:
            result = get_recommendations(**BASE_INPUT)
            assert result["soil_health_score"] == 65
            warnings_text = " ".join(result["warnings"]).lower()
            assert "gemini" in warnings_text
        finally:
            config_mock.GEMINI_API_KEY = original

    def test_gemini_partial_response_handled(self):
        """Partial Gemini response (missing some fields) should not crash."""
        partial = {
            "soil_health_score": 70,
            "soil_health_label": "Good",
            # missing many fields
        }
        with patch("services.recommendation_service._call_gemini",
                   return_value=partial):
            result = get_recommendations(**BASE_INPUT)
        # Should not crash, defaults should fill in
        assert "soil_health_score" in result
        assert isinstance(result["micronutrients"], list)
        assert isinstance(result["warnings"], list)

    def test_area_affects_total_quantity_in_fallback(self):
        """Larger area should increase total fertilizer quantity in fallback."""
        with patch("services.recommendation_service._call_gemini",
                   side_effect=Exception("force fallback")):
            result_small = get_recommendations(**{**BASE_INPUT, "area": 1.0})
            result_large = get_recommendations(**{**BASE_INPUT, "area": 5.0})
        cost_small = result_small["primary_fertilizer"]["estimated_cost_inr"]
        cost_large = result_large["primary_fertilizer"]["estimated_cost_inr"]
        assert cost_large > cost_small


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CROP-SPECIFIC NPK TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestCropSpecificNPK:

    def test_sugarcane_high_nitrogen_requirement(self):
        """Sugarcane should require highest N (250 kg/ha)."""
        result = _npk_status("SUGARCANE", n=100, p=50, k=80)
        assert result["nitrogen"]["required"] == 250

    def test_soyabean_low_nitrogen_requirement(self):
        """Soyabean fixes N, so requirement is low (30 kg/ha)."""
        result = _npk_status("SOYABEAN", n=25, p=50, k=40)
        assert result["nitrogen"]["required"] == 30

    def test_banana_high_potassium_requirement(self):
        """Banana needs highest K (300 kg/ha)."""
        result = _npk_status("BANANA", n=100, p=40, k=200)
        assert result["potassium"]["required"] == 300

    def test_groundnut_low_nitrogen_requirement(self):
        """Groundnut is legume — low N requirement (25 kg/ha)."""
        result = _npk_status("GROUNDNUT", n=20, p=40, k=40)
        assert result["nitrogen"]["required"] == 25

    def test_potato_high_potassium_requirement(self):
        """Potato needs high K (200 kg/ha)."""
        result = _npk_status("POTATO", n=100, p=60, k=150)
        assert result["potassium"]["required"] == 200

    def test_rice_nitrogen_optimal_at_120(self):
        """Rice needs 120 N — providing 120 should be Optimal."""
        result = _npk_status("RICE", n=120, p=60, k=60)
        assert result["nitrogen"]["status"] == "Optimal"

    def test_cotton_nitrogen_deficient_at_100(self):
        """Cotton needs 150 N — 100 is deficient."""
        result = _npk_status("COTTON", n=100, p=60, k=60)
        assert result["nitrogen"]["status"] == "Deficient"
        assert result["nitrogen"]["gap"] == 50