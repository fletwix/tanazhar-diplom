"""
Pydantic schemas for User endpoints.
"""

from pydantic import BaseModel, EmailStr, Field


# ── Request bodies ──────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6)
    weight_kg: float = Field(default=70.0, ge=20.0, le=300.0)


class UserLogin(BaseModel):
    email: str
    password: str


# ── Response bodies ─────────────────────────────────────────────

class UserRead(BaseModel):
    id: int
    username: str
    email: str
    weight_kg: float

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
