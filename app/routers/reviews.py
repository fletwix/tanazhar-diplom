"""
Review endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.review import Review
from app.models.route import Route
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewRead

router = APIRouter(prefix="/routes", tags=["reviews"])


@router.post("/{route_id}/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    route_id: int,
    body: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Review:
    """Leave a rating and review for a route."""
    # Check if route exists
    result = await db.execute(select(Route).where(Route.id == route_id))
    route = result.scalar_one_or_none()
    if route is None:
        raise HTTPException(status_code=404, detail="Route not found")
        
    # Check if user already reviewed
    existing = await db.execute(
        select(Review).where(
            (Review.route_id == route_id) & (Review.user_id == current_user.id)
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="You have already reviewed this route")
        
    review = Review(
        route_id=route.id,
        user_id=current_user.id,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@router.get("/{route_id}/reviews", response_model=list[ReviewRead])
async def get_reviews(
    route_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[Review]:
    """Get all reviews for a specific route."""
    result = await db.execute(
        select(Review)
        .where(Review.route_id == route_id)
        .order_by(Review.created_at.desc())
    )
    return list(result.scalars().all())
