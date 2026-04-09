"""
Point-of-Interest model with PostGIS geometry.
"""

import enum

from geoalchemy2 import Geometry
from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class POITypeEnum(str, enum.Enum):
    WATER = "water"
    CAMP = "camp"
    DANGER = "danger"
    VIEW = "view"


class POI(Base):
    __tablename__ = "pois"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), nullable=False)
    poi_type: Mapped[POITypeEnum] = mapped_column(
        Enum(POITypeEnum, name="poi_type_enum"),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    geom = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    # Relationships
    route: Mapped["Route"] = relationship(  # noqa: F821
        "Route", back_populates="pois",
    )
