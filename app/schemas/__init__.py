"""
Re-export all Pydantic schemas for convenient imports.
"""

from app.schemas.user import UserCreate, UserLogin, UserRead, Token
from app.schemas.route import (
    WaypointIn,
    RouteCreate,
    BBoxQuery,
    CoordinateOut,
    RouteRead,
    RouteListItem,
)
from app.schemas.poi import POICreate, POIRead
from app.schemas.review import ReviewCreate, ReviewRead
from app.schemas.energy import EnergyCalcRequest, EnergyCalcResponse

__all__ = [
    "UserCreate", "UserLogin", "UserRead", "Token",
    "WaypointIn", "RouteCreate", "BBoxQuery", "CoordinateOut",
    "RouteRead", "RouteListItem",
    "POICreate", "POIRead",
    "ReviewCreate", "ReviewRead",
    "EnergyCalcRequest", "EnergyCalcResponse",
]
