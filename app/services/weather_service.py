"""
OpenWeather API integration.
"""

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

settings = get_settings()

async def get_current_weather(lat: float, lon: float) -> dict:
    """Fetch current weather for a specific point."""
    if not settings.OPENWEATHER_API_KEY or settings.OPENWEATHER_API_KEY == "your-openweather-api-key":
        # Missing key handling
        pass

    url = f"{settings.OPENWEATHER_BASE_URL}/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            
            weather = data.get("weather", [{}])[0]
            main_temps = data.get("main", {})
            wind = data.get("wind", {})
            
            return {
                "temperature": main_temps.get("temp"),
                "feels_like": main_temps.get("feels_like"),
                "description": weather.get("description"),
                "wind_speed": wind.get("speed"),
                "icon": weather.get("icon"),
            }
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OpenWeather error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Weather service error: {str(e)}"
            )
