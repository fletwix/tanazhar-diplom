"""
Route model with PostGIS geometry.
"""

import enum

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, Enum, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DifficultyEnum(str, enum.Enum):
    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    geom = mapped_column(
        Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=True),
        nullable=True,
    )
    distance_km: Mapped[float] = mapped_column(Float, default=0.0)
    elevation_gain_m: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty: Mapped[DifficultyEnum] = mapped_column(
        Enum(DifficultyEnum, name="difficulty_enum"),
        default=DifficultyEnum.MEDIUM,
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    author: Mapped["User"] = relationship(  # noqa: F821
        "User", back_populates="routes",
    )
    pois: Mapped[list["POI"]] = relationship(  # noqa: F821
        "POI", back_populates="route", cascade="all, delete-orphan", lazy="selectin",
    )
    reviews: Mapped[list["Review"]] = relationship(  # noqa: F821
        "Review", back_populates="route", cascade="all, delete-orphan", lazy="selectin",
    )
