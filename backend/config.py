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
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Path to the trained ML model artifact (Phase 2)
MODEL_PATH: str = os.getenv("MODEL_PATH", "models/crop_yield_model.pkl")

# Server port (default 8000)
PORT: int = int(os.getenv("PORT", "8000"))
