"""
Re-export all ORM models so that Alembic and other code can simply
``from app.models import User, Route, POI, Review``.
"""

from app.models.user import User
from app.models.route import Route
from app.models.poi import POI
from app.models.review import Review

__all__ = ["User", "Route", "POI", "Review"]
