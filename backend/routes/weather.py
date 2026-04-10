"""
weather.py — GET /api/weather

Returns current weather data for a given location.
"""

from fastapi import APIRouter, Query
from models.schemas import WeatherResponse
from services.weather_service import get_weather

router = APIRouter()


@router.get("/weather", response_model=WeatherResponse, summary="Get current weather")
def weather(
    location: str = Query(..., description="City or region name", example="Pune, Maharashtra"),
) -> WeatherResponse:
    """Fetch current weather conditions for the specified location.

    **Query parameter**:
    - `location` — city or region name

    **Response** fields include live data from the OpenWeather API.
    Falls back to mock data with a console warning if the API call fails.
    """
    return get_weather(location)
