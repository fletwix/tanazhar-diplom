"""
Pydantic schemas for Route endpoints.
"""

from pydantic import BaseModel, Field


# ── Shared / nested ────────────────────────────────────────────

class WaypointIn(BaseModel):
    """A single [lon, lat] pair sent from the frontend."""
    lon: float = Field(..., ge=-180.0, le=180.0)
    lat: float = Field(..., ge=-90.0, le=90.0)


# ── Request bodies ──────────────────────────────────────────────

class RouteCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    difficulty: str = Field(default="MEDIUM", pattern=r"^(EASY|MEDIUM|HARD)$")
    is_public: bool = True
    waypoints: list[WaypointIn] = Field(..., min_length=2)


class BBoxQuery(BaseModel):
    """Bounding-box filter for spatial search."""
    min_lon: float = Field(..., ge=-180.0, le=180.0)
    min_lat: float = Field(..., ge=-90.0, le=90.0)
    max_lon: float = Field(..., ge=-180.0, le=180.0)
    max_lat: float = Field(..., ge=-90.0, le=90.0)


# ── Response bodies ─────────────────────────────────────────────

class CoordinateOut(BaseModel):
    lon: float
    lat: float


class RouteRead(BaseModel):
    id: int
    author_id: int
    title: str
    description: str | None = None
    distance_km: float
    elevation_gain_m: float
    difficulty: str
    is_public: bool
    rating: float | None = None
    reviews_count: int = 0
    coordinates: list[CoordinateOut] = []

    model_config = {"from_attributes": True}


class RouteListItem(BaseModel):
    id: int
    title: str
    distance_km: float
    elevation_gain_m: float
    difficulty: str
    author_id: int
    rating: float | None = None
    reviews_count: int = 0

    model_config = {"from_attributes": True}
