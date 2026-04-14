"""
Geo-endpoints for Routes and Points of Interest (POIs).
"""

import json

import gpxpy
import gpxpy.gpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.poi import POI
from app.models.review import Review
from app.models.route import Route
from app.models.user import User
from app.schemas.energy import EnergyCalcRequest, EnergyCalcResponse
from app.schemas.poi import POICreate, POIRead
from app.schemas.route import (
    BBoxQuery,
    CoordinateOut,
    RouteCreate,
    RouteListItem,
    RouteRead,
)
from app.services.routing_service import get_route_from_ors
from app.services.search_service import search_places
from app.services.weather_service import get_current_weather

router = APIRouter(prefix="/routes", tags=["routes"])


# ── Search Places (Yandex Search Maps API proxy) ───────────────

@router.get("/search")
async def search_nearby_places(
    text: str = Query(..., min_length=1),
    lon: float = Query(..., ge=-180.0, le=180.0),
    lat: float = Query(..., ge=-90.0, le=90.0),
    spn_lon: float = Query(0.1, ge=0.001, le=5.0),
    spn_lat: float = Query(0.1, ge=0.001, le=5.0),
) -> list[dict]:
    """Search for nearby businesses/places via Yandex Search Maps API."""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Search request: text=%s lon=%s lat=%s", text, lon, lat)
    try:
        places = await search_places(
            text=text, lon=lon, lat=lat,
            spn_lon=spn_lon, spn_lat=spn_lat,
        )
        logger.info("Search returned %d places", len(places))
        return places
    except Exception as e:
        logger.error("Search endpoint error: %s", e, exc_info=True)
        return []


# ── Weather (standalone, must be BEFORE /{route_id}) ────────────

@router.get("/weather")
async def get_weather_by_coords(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
) -> dict:
    """Get current weather at given coordinates (used by frontend)."""
    weather_data = await get_current_weather(lat=lat, lon=lon)
    return weather_data


# ── Create Route ────────────────────────────────────────────────

@router.post("/", response_model=RouteRead, status_code=status.HTTP_201_CREATED)
async def create_route(
    body: RouteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create a new route by sending waypoints to ORS and saving the geometry."""
    
    # Send waypoints to ORS
    route_data = await get_route_from_ors(body.waypoints)
    
    route = Route(
        author_id=current_user.id,
        title=body.title,
        description=body.description,
        difficulty=body.difficulty,
        is_public=body.is_public,
        distance_km=route_data["distance_km"],
        elevation_gain_m=route_data["elevation_gain_m"],
        geom=route_data["geometry_wkt"],
    )
    
    db.add(route)
    await db.commit()
    await db.refresh(route, ["pois"])
    
    # Prepare response coordinates
    coords = route_data["coordinates"]
    formatted_coords = [{"lon": c[0], "lat": c[1]} for c in coords]
    
    # Return as dict matching RouteRead schema, because SQLAlchemy instance doesn't have `coordinates`
    return {
        "id": route.id,
        "author_id": route.author_id,
        "title": route.title,
        "description": route.description,
        "distance_km": route.distance_km,
        "elevation_gain_m": route.elevation_gain_m,
        "difficulty": route.difficulty,
        "is_public": route.is_public,
        "coordinates": formatted_coords
    }


# ── Explore Spatial (BBox) ──────────────────────────────────────

@router.get("/explore", response_model=list[RouteListItem])
async def explore_routes(
    min_lon: float = Query(..., ge=-180.0, le=180.0),
    min_lat: float = Query(..., ge=-90.0, le=90.0),
    max_lon: float = Query(..., ge=-180.0, le=180.0),
    max_lat: float = Query(..., ge=-90.0, le=90.0),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Search for public routes within a bounding box using PostGIS ST_Intersects."""
    
    # Construct PostGIS ST_MakeEnvelope
    envelope = func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326)
    
    stmt = select(
        Route,
        func.avg(Review.rating).label("rating"),
        func.count(Review.id).label("reviews_count")
    ).outerjoin(
        Review, Route.id == Review.route_id
    ).where(
        Route.is_public.is_(True),
        func.ST_Intersects(Route.geom, envelope)
    ).group_by(Route.id)
    
    result = await db.execute(stmt)
    rows = result.all()
    
    routes = []
    for r in rows:
        routes.append({
            "id": r.Route.id,
            "title": r.Route.title,
            "distance_km": r.Route.distance_km,
            "elevation_gain_m": r.Route.elevation_gain_m,
            "difficulty": r.Route.difficulty,
            "author_id": r.Route.author_id,
            "rating": float(r.rating) if r.rating is not None else None,
            "reviews_count": r.reviews_count
        })
        
    return routes


# ── Retrieve Specific Route ─────────────────────────────────────

@router.get("/{route_id}", response_model=RouteRead)
async def get_route(
    route_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Fetch route details including POIs (requires manual coordinates extraction)."""
    
    stmt = select(
        Route,
        func.avg(Review.rating).label("rating"),
        func.count(Review.id).label("reviews_count")
    ).outerjoin(
        Review, Route.id == Review.route_id
    ).where(Route.id == route_id).options(selectinload(Route.pois)).group_by(Route.id)
    
    result = await db.execute(stmt)
    row = result.first()
    
    if row is None:
        raise HTTPException(status_code=404, detail="Route not found")
        
    route = row.Route
    rating = row.rating
    reviews_count = row.reviews_count
        
    # Extract coordinates from Geoalchemy2 WKBElement
    coords = []
    if route.geom is not None:
        shape = to_shape(route.geom)
        geom_dict = mapping(shape)
        if geom_dict["type"] == "LineString":
            coords = [{"lon": c[0], "lat": c[1]} for c in geom_dict["coordinates"]]
        elif geom_dict["type"] == "MultiLineString":
            # Just take the first line segment or flatten
            coords = [
                {"lon": c[0], "lat": c[1]} 
                for line in geom_dict["coordinates"] 
                for c in line
            ]

    # Return dictionary
    return {
        "id": route.id,
        "author_id": route.author_id,
        "title": route.title,
        "description": route.description,
        "distance_km": route.distance_km,
        "elevation_gain_m": route.elevation_gain_m,
        "difficulty": route.difficulty,
        "is_public": route.is_public,
        "rating": float(rating) if rating is not None else None,
        "reviews_count": reviews_count,
        "coordinates": coords
    }


# ── Create POI ──────────────────────────────────────────────────

@router.post("/{route_id}/pois", response_model=POIRead, status_code=status.HTTP_201_CREATED)
async def create_poi(
    route_id: int,
    body: POICreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Add a Point of Interest (POI) to a specific route."""
    
    # Check if route exists and user owns it
    result = await db.execute(select(Route).where(Route.id == route_id))
    route = result.scalar_one_or_none()
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
        
    if route.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this route")
        
    wkt_pt = f"SRID=4326;POINT({body.lon} {body.lat})"
    
    poi = POI(
        route_id=route.id,
        poi_type=body.poi_type,
        description=body.description,
        geom=wkt_pt,
    )
    
    db.add(poi)
    await db.commit()
    await db.refresh(poi)
    
    return {
        "id": poi.id,
        "route_id": poi.route_id,
        "poi_type": poi.poi_type,
        "description": poi.description,
        "lon": body.lon,
        "lat": body.lat
    }


# ── GPX Export ──────────────────────────────────────────────────

@router.get("/{route_id}/gpx", response_class=StreamingResponse)
async def export_gpx(
    route_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generate and stream a GPX file for the specified route."""
    stmt = select(Route).where(Route.id == route_id).options(selectinload(Route.pois))
    result = await db.execute(stmt)
    route = result.scalar_one_or_none()
    
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
        
    gpx = gpxpy.gpx.GPX()
    gpx.name = route.title
    gpx.description = route.description
    gpx.author_name = "TrailWeaver"
    
    # 1. Add Track
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx_track.name = f"Track: {route.title}"
    gpx.tracks.append(gpx_track)
    
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)
    
    if route.geom is not None:
        shape = to_shape(route.geom)
        geom_dict = mapping(shape)
        
        # We handle LineString simply here
        coords = []
        if geom_dict["type"] == "LineString":
            coords = geom_dict["coordinates"]
        elif geom_dict["type"] == "MultiLineString":
            for line in geom_dict["coordinates"]:
                coords.extend(line)
                
        for coord in coords:
            # Note: GeoJSON [lon, lat] -> GPX (lat, lon)
            # We don't have elevation from geometries right now without full 3D parsing, 
            # but we can provide the 2D track points.
            pt = gpxpy.gpx.GPXTrackPoint(latitude=coord[1], longitude=coord[0])
            gpx_segment.points.append(pt)

    # 2. Add POIs as Waypoints
    for poi in route.pois:
        poi_shape = to_shape(poi.geom)
        poi_geom = mapping(poi_shape)
        lon, lat = poi_geom["coordinates"]
        wpt = gpxpy.gpx.GPXWaypoint(latitude=lat, longitude=lon, name=poi.poi_type, description=poi.description)
        gpx.waypoints.append(wpt)
        
    xml_data = gpx.to_xml()
    
    headers = {
        "Content-Disposition": f'attachment; filename="route_{route_id}.gpx"'
    }
    
    # Streaming the XML string
    def iterfile():
        yield xml_data.encode("utf-8")

    return StreamingResponse(iterfile(), media_type="application/gpx+xml", headers=headers)


# ── Energy Calculator (Pandolf Equation) ────────────────────────

@router.post("/{route_id}/energy-calc", response_model=EnergyCalcResponse)
async def calculate_energy(
    route_id: int,
    body: EnergyCalcRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Calculate estimated calorie burn based on user weight, route distance/elevation,
    using a simplified constant-speed Pandolf equation approach.
    """
    stmt = select(Route).where(Route.id == route_id)
    result = await db.execute(stmt)
    route = result.scalar_one_or_none()
    
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
        
    W = current_user.weight_kg or 0.0
    L = body.backpack_weight_kg

    if W <= 0:
        raise HTTPException(
            status_code=400,
            detail="Вес пользователя не задан. Укажите вес в профиле при регистрации."
        )
    
    # Pandolf Equation for Walking Metabolism (Watts)
    # M = 1.5*W + 2.0*(W+L)*(L/W)^2 + n*(W+L)*(1.5*V^2 + 0.35*V*G)
    # V = Velocity (m/s), G = Grade (%)
    # Let's assume a simplified hiking constant: average speed V = 1.0 m/s (3.6 km/h)
    V = 1.0
    
    distance_m = route.distance_km * 1000.0
    # Average Grade = Elevation Gain / Distance
    # For Pandolf, Grade G is percentage (0 to ~20 usually)
    G = (route.elevation_gain_m / distance_m * 100.0) if distance_m > 0 else 0.0
    
    # Calculate Metabolic Rate in Watts (Joules/sec) for flat + uphill
    # n = terrain factor. Paved=1.0, Dirt=1.1, Loose sand=2.1, Snow=2.5. We use 1.2 for trails.
    n = 1.2 
    
    part1 = 1.5 * W
    part2 = 2.0 * (W + L) * ((L / W) ** 2) if W > 0 else 0
    part3 = n * (W + L) * (1.5 * (V**2) + 0.35 * V * G)
    
    M_watts = part1 + part2 + part3
    if M_watts < 0:
         M_watts = part1 # Fallback if math goes heavily negative down steep downhill
         
    # Time in seconds
    t_seconds = distance_m / V if V > 0 else 0.0
    
    # Total Energy = M(Joules/sec) * t(sec) = Total Joules
    # Convert Joules to kiloCalories (1 kcal = 4184 Joules)
    total_joules = M_watts * t_seconds
    total_kcal = total_joules / 4184.0
    
    return {
        "route_id": route_id,
        "distance_km": round(route.distance_km, 2),
        "elevation_gain_m": round(route.elevation_gain_m, 2),
        "user_weight_kg": W,
        "backpack_weight_kg": L,
        "total_calories_kcal": round(total_kcal, 2),
        "walking_time_hours": round(t_seconds / 3600.0, 2)
    }


# ── Weather Integration ─────────────────────────────────────────

@router.get("/{route_id}/weather")
async def get_route_weather(
    route_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get current weather at the starting point of the route."""
    stmt = select(Route).where(Route.id == route_id)
    result = await db.execute(stmt)
    route = result.scalar_one_or_none()
    
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
        
    if not route.geom:
        raise HTTPException(status_code=400, detail="Route has no geometry")
        
    shape_obj = to_shape(route.geom)
    geom_dict = mapping(shape_obj)
    
    # Extract starting coordinate
    lon, lat = 0.0, 0.0
    if geom_dict["type"] == "LineString" and geom_dict["coordinates"]:
        lon, lat = geom_dict["coordinates"][0][:2]
    elif geom_dict["type"] == "MultiLineString" and geom_dict["coordinates"]:
        lon, lat = geom_dict["coordinates"][0][0][:2]
        
    weather_data = await get_current_weather(lat=lat, lon=lon)
    return weather_data

