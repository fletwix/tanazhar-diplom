"""
OpenRouteService integration.
"""

import httpx
from fastapi import HTTPException, status
from shapely import force_2d
from shapely.geometry import shape

from app.core.config import get_settings
from app.schemas.route import WaypointIn

settings = get_settings()

async def get_route_from_ors(waypoints: list[WaypointIn]) -> dict:
    """
    Fetch walking directions from OpenRouteService.
    Returns parsed GeoJSON features, distance, ascent, and WKT.
    """
    if not settings.ORS_API_KEY or settings.ORS_API_KEY == "your-openrouteservice-api-key":
        # For testing purposes when API key is not configured, normally we would raise an error.
        # But we will let it attempt to connect or return a dummy response if preferred.
        pass

    # Format waypoints for ORS: [[lon, lat], [lon, lat]]
    coords = [[wp.lon, wp.lat] for wp in waypoints]
    
    url = f"{settings.ORS_BASE_URL}/v2/directions/foot-hiking/geojson"
    headers = {
        "Authorization": settings.ORS_API_KEY,
        "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
        "Content-Type": "application/json; charset=utf-8"
    }
    payload = {
        "coordinates": coords,
        "elevation": True
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers, timeout=15.0)
            response.raise_for_status()
            data = response.json()
            
            if "features" not in data or not data["features"]:
                raise ValueError("No route found.")
                
            feature = data["features"][0]
            geometry = feature["geometry"]  # GeoJSON LineString/MultiLineString
            
            summary = feature.get("properties", {}).get("summary", {})
            distance_m = summary.get("distance", 0.0)
            ascent_m = summary.get("ascent", 0.0)
            
            # WKT geometry for PostGIS
            # ORS returns 3D geometry (Z=elevation). We force 2D to match our PostGIS column.
            geom_shape = force_2d(shape(geometry))
            wkt_geom = f"SRID=4326;{geom_shape.wkt}"
            
            return {
                "distance_km": distance_m / 1000.0,
                "elevation_gain_m": ascent_m,
                "geometry_wkt": wkt_geom,
                "coordinates": geometry.get("coordinates", [])
            }

        except httpx.HTTPStatusError as e:
            # Note: For MVP or dummy testing, we can implement a fallback
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"OpenRouteService error: {e.response.text}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Routing service error: {str(e)}"
            )
