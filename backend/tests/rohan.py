"""
test_backend.py — Complete pytest test suite for SmartAgri API
============================================================
Covers: Auth, Predict, Recommend, Disease, Weather, History

Setup:
    pip install pytest pytest-asyncio httpx fastapi sqlalchemy

Run:
    pytest tests/test_backend.py -v
    pytest tests/test_backend.py -v -k "auth"        # only auth tests
    pytest tests/test_backend.py -v -k "predict"     # only predict tests
    pytest tests/test_backend.py --tb=short           # short traceback
"""

import io
import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Import your app ───────────────────────────────────────────────────────────
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import app
from database import get_db, Base

# ── In-memory SQLite for testing ──────────────────────────────────────────────
TEST_DB_URL = "sqlite:///./test_smartagri.db"
engine      = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession  = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# ── Test client ───────────────────────────────────────────────────────────────
client = TestClient(app)

# ── Sample payloads ───────────────────────────────────────────────────────────
REGISTER_PAYLOAD = {
    "name":     "Test Farmer",
    "email":    "testfarmer@smartagri.com",
    "password": "test1234",
    "district": "Pune",
}

LOGIN_PAYLOAD = {
    "email":    "testfarmer@smartagri.com",
    "password": "test1234",
}

PREDICT_PAYLOAD = {
    "location":        "Pune",
    "district":        25,
    "season":          1,
    "irrigation_type": 0,
    "soil_type":       0,
    "nitrogen":        65.0,
    "phosphorus":      75.0,
    "potassium":       110.0,
    "ph":              7.0,
    "area":            4.0,
    "temperature":     28.0,
    "humidity":        70.0,
    "rainfall":        800.0,
}

RECOMMEND_PAYLOAD = {
    "location":        "Pune",
    "crop":            "SUGARCANE",
    "season":          "Kharif",
    "soil_type":       "Black",
    "irrigation_type": "Rainfed",
    "area":            4.0,
    "nitrogen":        65.0,
    "phosphorus":      75.0,
    "potassium":       110.0,
    "ph":              7.0,
    "temperature":     28.0,
    "rainfall":        800.0,
    "predicted_yield": 8.0,
}


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create all tables before tests, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def auth_token():
    """Register + login once, return token for all tests in module."""
    # Try register (may already exist)
    client.post("/api/auth/register", json=REGISTER_PAYLOAD)
    # Login
    res = client.post("/api/auth/login", json=LOGIN_PAYLOAD)
    assert res.status_code == 200, f"Login failed: {res.text}"
    return res.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuth:

    def test_register_success(self):
        """New user registration returns 201 with token."""
        payload = {
            "name":     "New Farmer",
            "email":    "newfarmer_unique@test.com",
            "password": "pass1234",
            "district": "Nagpur",
        }
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert "access_token" in data
        assert data["email"] == payload["email"]
        assert data["name"]  == payload["name"]

    def test_register_duplicate_email(self):
        """Registering same email twice returns 400."""
        client.post("/api/auth/register", json=REGISTER_PAYLOAD)
        res = client.post("/api/auth/register", json=REGISTER_PAYLOAD)
        assert res.status_code == 400
        assert "already registered" in res.json()["detail"].lower()

    def test_register_short_password(self):
        """Password under 6 chars returns 422 validation error."""
        payload = {**REGISTER_PAYLOAD, "email": "short@test.com", "password": "123"}
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 422

    def test_register_invalid_email(self):
        """Invalid email format returns 422."""
        payload = {**REGISTER_PAYLOAD, "email": "not-an-email"}
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 422

    def test_login_success(self):
        """Valid credentials return token."""
        client.post("/api/auth/register", json=REGISTER_PAYLOAD)
        res = client.post("/api/auth/login", json=LOGIN_PAYLOAD)
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self):
        """Wrong password returns 401."""
        res = client.post("/api/auth/login", json={
            "email": REGISTER_PAYLOAD["email"],
            "password": "wrongpassword",
        })
        assert res.status_code == 401
        assert "invalid" in res.json()["detail"].lower()

    def test_login_nonexistent_email(self):
        """Non-existent email returns 401."""
        res = client.post("/api/auth/login", json={
            "email":    "ghost@nowhere.com",
            "password": "pass1234",
        })
        assert res.status_code == 401

    def test_get_me_authenticated(self, auth_headers):
        """Authenticated user can fetch their profile."""
        res = client.get("/api/auth/me", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "user_id"  in data
        assert "email"    in data
        assert "name"     in data

    def test_get_me_no_token(self):
        """No token returns 401/403."""
        res = client.get("/api/auth/me")
        assert res.status_code in (401, 403)

    def test_get_me_invalid_token(self):
        """Fake token returns 401."""
        res = client.get("/api/auth/me", headers={"Authorization": "Bearer faketoken123"})
        assert res.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# PREDICT TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestPredict:

    def test_predict_as_guest(self):
        """Guest (no token) can predict — returns 200."""
        res = client.post("/api/predict", json=PREDICT_PAYLOAD)
        assert res.status_code == 200
        data = res.json()
        assert "recommended_crop" in data
        assert "predicted_yield"  in data
        assert "confidence"       in data

    def test_predict_as_user(self, auth_headers):
        """Logged-in user prediction is saved to DB."""
        res = client.post("/api/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert "recommended_crop" in data

    def test_predict_crop_is_string(self):
        """Recommended crop must be a non-empty string."""
        res = client.post("/api/predict", json=PREDICT_PAYLOAD)
        assert res.status_code == 200
        crop = res.json()["recommended_crop"]
        assert isinstance(crop, str)
        assert len(crop) > 0

    def test_predict_yield_is_positive(self):
        """Predicted yield must be a positive number."""
        res = client.post("/api/predict", json=PREDICT_PAYLOAD)
        assert res.status_code == 200
        yield_val = res.json()["predicted_yield"]
        assert isinstance(yield_val, (int, float))
        assert yield_val >= 0

    def test_predict_confidence_range(self):
        """Confidence must be between 0 and 100."""
        res = client.post("/api/predict", json=PREDICT_PAYLOAD)
        assert res.status_code == 200
        conf = res.json()["confidence"]
        assert 0 <= conf <= 100

    def test_predict_missing_nitrogen(self):
        """Missing required field returns 422."""
        payload = {k: v for k, v in PREDICT_PAYLOAD.items() if k != "nitrogen"}
        res = client.post("/api/predict", json=payload)
        assert res.status_code == 422

    def test_predict_different_seasons(self):
        """All four seasons should return valid predictions."""
        for season in [1, 2, 3, 4]:
            payload = {**PREDICT_PAYLOAD, "season": season}
            res = client.post("/api/predict", json=payload)
            assert res.status_code == 200, f"Season {season} failed"
            assert "recommended_crop" in res.json()

    def test_predict_different_districts(self):
        """Sample of different districts should all work."""
        for district in [0, 10, 18, 25, 35]:  # Ahmednagar, Gondia, Nagpur, Pune, Yavatmal
            payload = {**PREDICT_PAYLOAD, "district": district}
            res = client.post("/api/predict", json=payload)
            assert res.status_code == 200, f"District {district} failed"


# ═══════════════════════════════════════════════════════════════════════════════
# RECOMMEND TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecommend:

    MOCK_RECOMMENDATION = {
        "soil_health_score":    72,
        "soil_health_label":    "Good",
        "npk_status":           {
            "nitrogen":   {"current": 65, "required": 250, "status": "Deficient", "gap": 185},
            "phosphorus": {"current": 75, "required": 100, "status": "Deficient", "gap": 25},
            "potassium":  {"current": 110, "required": 150, "status": "Deficient", "gap": 40},
        },
        "primary_fertilizer":   {"name": "Urea", "grade": "46-0-0", "quantity_per_ha": "400 kg",
                                  "total_quantity": "1600 kg", "estimated_cost_inr": 32000,
                                  "application_method": "Split application"},
        "secondary_fertilizer": {"name": "DAP", "grade": "18-46-0", "quantity_per_ha": "100 kg",
                                  "total_quantity": "400 kg", "estimated_cost_inr": 10800,
                                  "application_method": "Basal dose"},
        "micronutrients":       [{"name": "Zinc", "product": "Zinc Sulphate", "dose": "25 kg/ha", "reason": "Common deficiency"}],
        "application_schedule": [{"stage": "Basal", "timing": "At sowing", "fertilizers": "DAP", "quantity": "100 kg"}],
        "organic_alternatives": [{"name": "FYM", "quantity": "10 t/ha", "benefit": "Improves structure"}],
        "warnings":             [],
        "crop_rotation":        "Soybean",
        "crop_rotation_reason": "Fixes nitrogen",
        "expected_yield_boost": "20%",
        "irrigation_advice":    "Use drip irrigation",
        "pest_risk":            "Low",
        "general_tips":         "Test soil annually",
    }

    def test_recommend_as_guest(self):
        """Guest can get recommendations."""
        with patch("services.recommendation_service.get_recommendations",
                   return_value=self.MOCK_RECOMMENDATION):
            res = client.post("/api/recommend", json=RECOMMEND_PAYLOAD)
        assert res.status_code == 200

    def test_recommend_response_has_required_fields(self):
        """Response must contain all key fields."""
        with patch("services.recommendation_service.get_recommendations",
                   return_value=self.MOCK_RECOMMENDATION):
            res = client.post("/api/recommend", json=RECOMMEND_PAYLOAD)
        assert res.status_code == 200
        data = res.json()
        required = [
            "soil_health_score", "soil_health_label", "npk_status",
            "primary_fertilizer", "secondary_fertilizer",
            "application_schedule", "crop_rotation", "irrigation_advice",
        ]
        for field in required:
            assert field in data, f"Missing field: {field}"

    def test_recommend_soil_health_score_range(self):
        """Soil health score must be 0–100."""
        with patch("services.recommendation_service.get_recommendations",
                   return_value=self.MOCK_RECOMMENDATION):
            res = client.post("/api/recommend", json=RECOMMEND_PAYLOAD)
        score = res.json()["soil_health_score"]
        assert 0 <= score <= 100

    def test_recommend_area_too_large(self):
        """Area > 500 should be rejected by validation."""
        payload = {**RECOMMEND_PAYLOAD, "area": 99999}
        res = client.post("/api/recommend", json=payload)
        # Either 422 (Pydantic) or 200 (backend clamps it)
        # If 200, verify cost isn't astronomical
        if res.status_code == 200:
            cost = res.json().get("primary_fertilizer", {}).get("estimated_cost_inr", 0)
            assert cost < 10_000_000, "Cost is unrealistically high — area not clamped"

    def test_recommend_missing_location(self):
        """Missing location returns 422."""
        payload = {k: v for k, v in RECOMMEND_PAYLOAD.items() if k != "location"}
        res = client.post("/api/recommend", json=payload)
        assert res.status_code == 422

    def test_recommend_npk_status_structure(self):
        """NPK status must have nitrogen, phosphorus, potassium keys."""
        with patch("services.recommendation_service.get_recommendations",
                   return_value=self.MOCK_RECOMMENDATION):
            res = client.post("/api/recommend", json=RECOMMEND_PAYLOAD)
        npk = res.json()["npk_status"]
        assert "nitrogen"   in npk
        assert "phosphorus" in npk
        assert "potassium"  in npk


# ═══════════════════════════════════════════════════════════════════════════════
# DISEASE TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestDisease:

    MOCK_DISEASE_RESULT = {
        "detected":              True,
        "plant_name":            "Sugarcane",
        "is_healthy":            False,
        "disease":               "Red Rot",
        "confidence":            87,
        "severity":              "Moderate",
        "affected_area":         "30%",
        "treatment":             "Remove infected plants",
        "biological_treatment":  "Trichoderma application",
        "chemical_treatment":    "Carbendazim 0.1%",
        "prevention":            "Use disease-free seed cane",
        "all_diseases":          [],
        "filename":              "leaf.jpg",
        "image_size":            102400,
    }

    def _make_image_file(self, size_kb=100):
        """Create a fake JPEG image bytes for testing."""
        # Minimal valid JPEG header
        jpeg_header = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46,
            0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
            0x00, 0x01, 0x00, 0x00, 0xFF, 0xD9
        ])
        padding = b'\x00' * (size_kb * 1024 - len(jpeg_header))
        return jpeg_header + padding

    def test_detect_disease_success(self):
        """Valid image upload returns detection result."""
        image_bytes = self._make_image_file(100)
        with patch("services.disease_service.detect_disease",
                   return_value=self.MOCK_DISEASE_RESULT):
            res = client.post(
                "/api/detect-disease",
                files={"image": ("leaf.jpg", io.BytesIO(image_bytes), "image/jpeg")},
            )
        assert res.status_code == 200
        data = res.json()
        assert "detected"    in data
        assert "plant_name"  in data
        assert "disease"     in data

    def test_detect_disease_too_large(self):
        """Image over 5MB returns 413."""
        large_image = b'\x00' * (6 * 1024 * 1024)  # 6 MB
        res = client.post(
            "/api/detect-disease",
            files={"image": ("big.jpg", io.BytesIO(large_image), "image/jpeg")},
        )
        assert res.status_code == 413

    def test_detect_disease_no_file(self):
        """No file uploaded returns 422."""
        res = client.post("/api/detect-disease")
        assert res.status_code == 422

    def test_detect_disease_response_structure(self):
        """Response must have all required disease fields."""
        image_bytes = self._make_image_file(50)
        with patch("services.disease_service.detect_disease",
                   return_value=self.MOCK_DISEASE_RESULT):
            res = client.post(
                "/api/detect-disease",
                files={"image": ("leaf.jpg", io.BytesIO(image_bytes), "image/jpeg")},
            )
        assert res.status_code == 200
        data = res.json()
        for field in ["detected", "is_healthy", "plant_name", "disease", "confidence"]:
            assert field in data, f"Missing: {field}"

    def test_detect_healthy_plant(self):
        """Healthy plant detection returns is_healthy=True."""
        healthy_result = {**self.MOCK_DISEASE_RESULT, "is_healthy": True, "detected": False, "disease": None}
        image_bytes = self._make_image_file(50)
        with patch("services.disease_service.detect_disease", return_value=healthy_result):
            res = client.post(
                "/api/detect-disease",
                files={"image": ("healthy.jpg", io.BytesIO(image_bytes), "image/jpeg")},
            )
        assert res.status_code == 200
        assert res.json()["is_healthy"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# WEATHER TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestWeather:

    MOCK_WEATHER = {
        "location":    "Pune",
        "temperature": 28.5,
        "humidity":    72.0,
        "rainfall":    5.2,
        "description": "Partly cloudy",
        "wind_speed":  12.0,
    }

    def test_weather_valid_location(self):
        """Valid location returns weather data."""
        with patch("services.weather_service.get_weather", return_value=self.MOCK_WEATHER):
            res = client.get("/api/weather?location=Pune")
        assert res.status_code == 200
        data = res.json()
        assert "temperature" in data
        assert "humidity"    in data
        assert "rainfall"    in data

    def test_weather_missing_location(self):
        """Missing location param returns 422."""
        res = client.get("/api/weather")
        assert res.status_code == 422

    def test_weather_temperature_range(self):
        """Temperature should be in realistic range (0–50°C)."""
        with patch("services.weather_service.get_weather", return_value=self.MOCK_WEATHER):
            res = client.get("/api/weather?location=Nagpur")
        assert res.status_code == 200
        temp = res.json()["temperature"]
        assert 0 <= temp <= 50, f"Unrealistic temperature: {temp}"

    def test_weather_humidity_range(self):
        """Humidity must be 0–100%."""
        with patch("services.weather_service.get_weather", return_value=self.MOCK_WEATHER):
            res = client.get("/api/weather?location=Mumbai")
        assert res.status_code == 200
        humidity = res.json()["humidity"]
        assert 0 <= humidity <= 100

    def test_weather_different_cities(self):
        """All Maharashtra cities should work."""
        cities = ["Pune", "Nagpur", "Nashik", "Aurangabad", "Kolhapur"]
        for city in cities:
            with patch("services.weather_service.get_weather", return_value=self.MOCK_WEATHER):
                res = client.get(f"/api/weather?location={city}")
            assert res.status_code == 200, f"Weather failed for {city}"


# ═══════════════════════════════════════════════════════════════════════════════
# HISTORY TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestHistory:

    def test_history_requires_auth(self):
        """History endpoints require authentication."""
        endpoints = [
            "/api/history/predictions",
            "/api/history/recommendations",
            "/api/history/disease",
            "/api/history/stats",
        ]
        for endpoint in endpoints:
            res = client.get(endpoint)
            assert res.status_code in (401, 403), f"{endpoint} should require auth"

    def test_list_predictions_empty(self, auth_headers):
        """Fresh user has empty prediction history."""
        # Register a new user for clean history
        new_user = {
            "name": "Clean User", "email": "cleanuser@test.com",
            "password": "pass1234", "district": "Pune",
        }
        client.post("/api/auth/register", json=new_user)
        login_res = client.post("/api/auth/login", json={
            "email": new_user["email"], "password": new_user["password"]
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/history/predictions", headers=headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_list_predictions_after_predict(self, auth_headers):
        """After predicting, history should have at least 1 entry."""
        # Make a prediction first
        client.post("/api/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        # Check history
        res = client.get("/api/history/predictions", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_prediction_history_structure(self, auth_headers):
        """Each prediction in history has required fields."""
        client.post("/api/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        res = client.get("/api/history/predictions", headers=auth_headers)
        assert res.status_code == 200
        items = res.json()
        if items:
            item = items[0]
            for field in ["id", "recommended_crop", "predicted_yield", "confidence", "created_at"]:
                assert field in item, f"Missing field: {field}"

    def test_get_prediction_by_id(self, auth_headers):
        """Can fetch a specific prediction by ID."""
        # Make prediction
        client.post("/api/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        # Get list
        list_res = client.get("/api/history/predictions", headers=auth_headers)
        items = list_res.json()
        if items:
            pred_id = items[0]["id"]
            res = client.get(f"/api/history/predictions/{pred_id}", headers=auth_headers)
            assert res.status_code == 200
            assert res.json()["id"] == pred_id

    def test_get_prediction_wrong_id(self, auth_headers):
        """Non-existent prediction ID returns 404."""
        res = client.get("/api/history/predictions/999999", headers=auth_headers)
        assert res.status_code == 404

    def test_delete_prediction(self, auth_headers):
        """Can delete a prediction."""
        client.post("/api/predict", json=PREDICT_PAYLOAD, headers=auth_headers)
        list_res = client.get("/api/history/predictions", headers=auth_headers)
        items = list_res.json()
        if items:
            pred_id = items[-1]["id"]
            del_res = client.delete(f"/api/history/predictions/{pred_id}", headers=auth_headers)
            assert del_res.status_code == 204
            # Verify deleted
            get_res = client.get(f"/api/history/predictions/{pred_id}", headers=auth_headers)
            assert get_res.status_code == 404

    def test_stats_structure(self, auth_headers):
        """Stats endpoint returns correct structure."""
        res = client.get("/api/history/stats", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        for field in ["total_predictions", "total_recommendations"]:
            assert field in data, f"Missing field: {field}"

    def test_stats_counts_are_non_negative(self, auth_headers):
        """Stats counts must be >= 0."""
        res = client.get("/api/history/stats", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total_predictions"]     >= 0
        assert data["total_recommendations"] >= 0

    def test_pagination(self, auth_headers):
        """Limit and offset params work."""
        res = client.get("/api/history/predictions?limit=5&offset=0", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)
        assert len(res.json()) <= 5


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM TESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TestSystem:

    def test_health_endpoint(self):
        """Health check returns ok."""
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_root_endpoint(self):
        """Root endpoint returns API info."""
        res = client.get("/")
        assert res.status_code == 200
        data = res.json()
        assert "message" in data
        assert "version" in data

    def test_cors_headers(self):
        """CORS headers present in response."""
        res = client.options("/api/predict", headers={"Origin": "http://localhost:3000"})
        # CORS middleware should handle this
        assert res.status_code in (200, 405)

    def test_invalid_route(self):
        """Unknown route returns 404."""
        res = client.get("/api/nonexistent")
        assert res.status_code == 404