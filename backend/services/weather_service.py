"""
weather_service.py — Weather data retrieval.

Phase 3 will replace the mock below with a live call to the OpenWeather API
using config.OPENWEATHER_API_KEY.
"""

from __future__ import annotations

from models.schemas import WeatherResponse


# Mock response — matches MOCK_WEATHER in frontend/js/api.js
_MOCK: dict = {
    "temperature": 28,
    "humidity": 65,
    "rainfall": 120,
    "wind_speed": 12,
    "description": "Partly Cloudy",
    "icon": "⛅",
}


def get_weather(location: str) -> WeatherResponse:
    """Return current weather data for the given location.

    Args:
        location: City or region name supplied by the user.

    Returns:
        WeatherResponse with mock data until the OpenWeather integration is
        added in Phase 3.
    """
    # TODO (Phase 3): call OpenWeather API with config.OPENWEATHER_API_KEY.
    return WeatherResponse(location=location, **_MOCK)
