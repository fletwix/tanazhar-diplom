"""
Pydantic schemas for Review endpoints.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class ReviewRead(BaseModel):
    id: int
    route_id: int
    user_id: int
    rating: int
    comment: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
