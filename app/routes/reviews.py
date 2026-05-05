from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import get_db
from app.models import Extraction, JobStatus, Review, ReviewExtraction, ReviewStatus
from app.schemas import ReviewCreateRequest, ReviewResponse, ReviewUpdateRequest
from app.services.reviewer import run_review_analysis, update_review_decision
from app.worker import enqueue

router = APIRouter()


@router.post("/", response_model=ReviewResponse)
async def create_review(
    request: ReviewCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a review from a set of completed extractions, then run LLM analysis."""
    # Validate all extractions exist and are completed
    for eid in request.extraction_ids:
        extraction = await db.get(Extraction, eid)
        if not extraction:
            raise HTTPException(status_code=404, detail=f"Extraction {eid} not found")
        if extraction.status != JobStatus.completed:
            raise HTTPException(
                status_code=400,
                detail=f"Extraction {eid} is not completed (status: {extraction.status.value})",
            )

    review = Review(status=ReviewStatus.pending)
    db.add(review)
    await db.flush()

    for eid in request.extraction_ids:
        link = ReviewExtraction(review_id=review.id, extraction_id=eid)
        db.add(link)

    await db.commit()

    # Reload with links
    result = await db.execute(
        select(Review).options(selectinload(Review.extraction_links)).where(Review.id == review.id)
    )
    review = result.scalar_one()

    await enqueue(run_review_analysis, review.id)

    return ReviewResponse.from_orm_with_json(review)


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(review_id: int, db: AsyncSession = Depends(get_db)):
    """Get a review by ID."""
    result = await db.execute(
        select(Review).options(selectinload(Review.extraction_links)).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return ReviewResponse.from_orm_with_json(review)


@router.patch("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    request: ReviewUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a review (human-in-the-loop decision)."""
    result = await db.execute(
        select(Review).options(selectinload(Review.extraction_links)).where(Review.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.status != ReviewStatus.ready_for_review:
        raise HTTPException(
            status_code=400,
            detail=f"Review is not ready for decision (status: {review.status.value})",
        )

    await update_review_decision(review, request.decision, request.reviewer_notes, db)

    # Reload
    result = await db.execute(
        select(Review).options(selectinload(Review.extraction_links)).where(Review.id == review_id)
    )
    review = result.scalar_one()
    return ReviewResponse.from_orm_with_json(review)


@router.get("/", response_model=list[ReviewResponse])
async def list_reviews(db: AsyncSession = Depends(get_db)):
    """List all reviews."""
    result = await db.execute(
        select(Review)
        .options(selectinload(Review.extraction_links))
        .order_by(Review.created_at.desc())
    )
    return [ReviewResponse.from_orm_with_json(r) for r in result.scalars().all()]
