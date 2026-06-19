"""
config.py — Application configuration.

Reads settings from environment variables (or a .env file).
Placeholders are included for API keys that will be wired up in later phases.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# External API keys (to be filled in .env for Phase 3 / Phase 5)
OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5/weather"
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# Plant.id API — used for real plant disease detection (Phase 4)
# Sign up at https://app.plant.id/ to obtain a key.
PLANT_ID_API_KEY: str = os.getenv("PLANT_ID_API_KEY", "")
PLANT_ID_API_URL: str = "https://api.plant.id/v2/health_assessment"

# Paths to the trained ML model artifacts
CROP_MODEL_PATH: str = os.getenv("CROP_MODEL_PATH", "models/crop_model.pkl")
YIELD_MODEL_PATH: str = os.getenv("YIELD_MODEL_PATH", "models/yield_model.pkl")
LABEL_ENCODER_PATH: str = os.getenv("LABEL_ENCODER_PATH", "models/label_encoder.pkl")

# Server port (default 8000)
PORT: int = int(os.getenv("PORT", "8000"))
