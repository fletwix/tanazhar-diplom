"""
Pydantic schemas for energy / calorie calculator.
"""

from pydantic import BaseModel, Field


class EnergyCalcRequest(BaseModel):
    backpack_weight_kg: float = Field(default=10.0, ge=0.0, le=60.0)


class EnergyCalcResponse(BaseModel):
    route_id: int
    distance_km: float
    elevation_gain_m: float
    user_weight_kg: float
    backpack_weight_kg: float
    total_calories_kcal: float
    walking_time_hours: float
