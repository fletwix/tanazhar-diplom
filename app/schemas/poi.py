"""
Pydantic schemas for POI endpoints.
"""

from pydantic import BaseModel, Field


class POICreate(BaseModel):
    poi_type: str = Field(..., pattern=r"^(water|camp|danger|view)$")
    description: str | None = None
    lon: float = Field(..., ge=-180.0, le=180.0)
    lat: float = Field(..., ge=-90.0, le=90.0)


class POIRead(BaseModel):
    id: int
    route_id: int
    poi_type: str
    description: str | None = None
    lon: float
    lat: float

    model_config = {"from_attributes": True}
