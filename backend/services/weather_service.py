"""
weather_service.py — Weather data retrieval.

Calls the OpenWeather API using config.OPENWEATHER_API_KEY and falls back
to mock data on any error.
"""

from __future__ import annotations

import logging

import httpx

from fastapi import HTTPException

import config
from models.schemas import WeatherResponse

logger = logging.getLogger(__name__)

# Seconds to wait for the OpenWeather API to respond
_API_TIMEOUT: int = 10

# Icon code → emoji mapping
WEATHER_ICONS: dict[str, str] = {
    "01d": "☀️", "01n": "🌙",
    "02d": "⛅", "02n": "☁️",
    "03d": "☁️", "03n": "☁️",
    "04d": "☁️", "04n": "☁️",
    "09d": "🌧️", "09n": "🌧️",
    "10d": "🌦️", "10n": "🌧️",
    "11d": "⛈️", "11n": "⛈️",
    "13d": "❄️", "13n": "❄️",
    "50d": "🌫️", "50n": "🌫️",
}

# Mock response — fallback when the API call fails
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

    Fetches live data from the OpenWeather API.  Falls back to mock data
    gracefully on any error (network issue, invalid city, etc.).

    Args:
        location: City or region name supplied by the user.

    Returns:
        WeatherResponse with live or mock weather data.

    Raises:
        HTTPException: 503 if OPENWEATHER_API_KEY is not configured.
    """
    if not config.OPENWEATHER_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Weather service unavailable: OPENWEATHER_API_KEY is not configured",
        )
    try:
        params = {
            "q": location,
            "appid": config.OPENWEATHER_API_KEY,
            "units": "metric",
        }
        response = httpx.get(config.OPENWEATHER_BASE_URL, params=params, timeout=_API_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        icon_code: str = data["weather"][0]["icon"]
        icon_emoji: str = WEATHER_ICONS.get(icon_code, "🌡️")

        # rainfall: prefer 1-hour bucket, fall back to 3-hour, then 0
        rain_data: dict = data.get("rain", {})
        rainfall: float = rain_data.get("1h", rain_data.get("3h", 0))

        # wind speed: convert m/s → km/h
        wind_speed: float = round(data["wind"]["speed"] * 3.6, 1)

        return WeatherResponse(
            location=data.get("name", location),
            temperature=round(data["main"]["temp"], 1),
            humidity=data["main"]["humidity"],
            rainfall=rainfall,
            wind_speed=wind_speed,
            description=data["weather"][0]["description"].capitalize(),
            icon=icon_emoji,
        )
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "OpenWeather API returned HTTP %s for %r — returning mock data",
            exc.response.status_code,
            location,
        )
    except httpx.RequestError as exc:
        logger.warning(
            "OpenWeather API request failed for %r (%s) — returning mock data",
            location,
            exc,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Unexpected error fetching weather for %r: %s — returning mock data", location, exc)
    return WeatherResponse(location=location, is_mock=True, **_MOCK)
