"""
Database Seeding script for TrailWeaver.
Populates the database with initial users, routes, POIs, and reviews.
"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import async_session, engine
from app.core.security import hash_password
from app.models.user import User
from app.models.route import Route
from app.models.poi import POI
from app.models.review import Review

async def seed_data():
    async with async_session() as session:
        # Check if users already exist
        user_result = await session.execute(select(User).where(User.username == "test_user"))
        if user_result.scalar_one_or_none() is not None:
            print("Data already seeded. Skipping.")
            return

        print("Seeding database...")
        
        # 1. Create a user
        user = User(
            username="test_user",
            email="test@example.com",
            hashed_password=hash_password("password123"),
            weight_kg=75.0
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"Created User: {user.username}")

        # 2. Create a route (mock WKT for a simple path around a park)
        # 43.238949, 76.889709 (Almaty, KZ - example coordinates)
        wkt_linestring = "SRID=4326;LINESTRING(76.8897 43.2389, 76.8907 43.2389, 76.8907 43.2399, 76.8897 43.2399)"
        route = Route(
            author_id=user.id,
            title="Almaty City Walk",
            description="A beautiful short walk in the city center.",
            distance_km=0.8,
            elevation_gain_m=10.0,
            difficulty="EASY",
            is_public=True,
            geom=wkt_linestring
        )
        session.add(route)
        await session.commit()
        await session.refresh(route)
        print(f"Created Route: {route.title}")

        # 3. Create POIs
        poi_wkt_1 = "SRID=4326;POINT(76.8897 43.2389)"
        poi_1 = POI(
            route_id=route.id,
            poi_type="VIEW",
            description="Start of the walk, nice view.",
            geom=poi_wkt_1
        )
        
        poi_wkt_2 = "SRID=4326;POINT(76.8907 43.2399)"
        poi_2 = POI(
            route_id=route.id,
            poi_type="WATER",
            description="Drinking fountain.",
            geom=poi_wkt_2
        )
        session.add_all([poi_1, poi_2])
        await session.commit()
        print("Created POIs")

        # 4. Create a review
        review = Review(
            route_id=route.id,
            user_id=user.id,
            rating=5,
            comment="Awesome walk for a sunny day!"
        )
        session.add(review)
        await session.commit()
        print("Created Review")
        
        print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_data())
