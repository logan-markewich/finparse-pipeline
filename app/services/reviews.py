"""Review CRUD service."""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app import db
from app.models import (
    Extraction,
    JobStatus,
    Review,
    ReviewDecision,
    ReviewExtraction,
    ReviewStatus,
)
from app.services.reviewer import run_review_analysis
from app.worker import enqueue


class ExtractionNotFoundError(Exception):
    def __init__(self, extraction_id: int):
        self.extraction_id = extraction_id
        super().__init__(f"Extraction {extraction_id} not found")


class ExtractionNotCompletedError(Exception):
    def __init__(self, extraction_id: int, status: str):
        self.extraction_id = extraction_id
        self.status = status
        super().__init__(f"Extraction {extraction_id} not completed (status: {status})")


class ReviewNotFoundError(Exception):
    pass


class ReviewNotReadyError(Exception):
    def __init__(self, status: str):
        self.status = status
        super().__init__(f"Review is not ready for decision (status: {status})")


async def create_review(extraction_ids: list[int]) -> Review:
    """Validate extractions, create a review, and enqueue LlamaParse analysis."""
    async with db.async_session() as session:
        for eid in extraction_ids:
            extraction = await session.get(Extraction, eid)
            if not extraction:
                raise ExtractionNotFoundError(eid)
            if extraction.status != JobStatus.completed:
                raise ExtractionNotCompletedError(eid, extraction.status.value)

        review = Review(status=ReviewStatus.pending)
        session.add(review)
        await session.flush()

        for eid in extraction_ids:
            link = ReviewExtraction(review_id=review.id, extraction_id=eid)
            session.add(link)

        await session.commit()

        result = await session.execute(
            select(Review)
            .options(selectinload(Review.extraction_links))
            .where(Review.id == review.id)
        )
        review = result.scalar_one()

    await enqueue(run_review_analysis, review.id)
    return review


async def get_review(review_id: int) -> Review | None:
    async with db.async_session() as session:
        result = await session.execute(
            select(Review)
            .options(selectinload(Review.extraction_links))
            .where(Review.id == review_id)
        )
        return result.scalar_one_or_none()


async def get_all_reviews() -> list[Review]:
    async with db.async_session() as session:
        result = await session.execute(
            select(Review)
            .options(selectinload(Review.extraction_links))
            .order_by(Review.created_at.desc())
        )
        return list(result.scalars().all())


async def update_review(
    review_id: int,
    decision: ReviewDecision,
    reviewer_notes: str | None,
) -> Review:
    """Record the human reviewer's decision and return the updated review."""
    async with db.async_session() as session:
        result = await session.execute(
            select(Review)
            .options(selectinload(Review.extraction_links))
            .where(Review.id == review_id)
        )
        review = result.scalar_one_or_none()
        if not review:
            raise ReviewNotFoundError
        if review.status != ReviewStatus.ready_for_review:
            raise ReviewNotReadyError(review.status.value)

        review.decision = decision
        review.reviewer_notes = reviewer_notes
        review.status = ReviewStatus.approved if (
            decision == ReviewDecision.approved
        ) else ReviewStatus.rejected
        await session.commit()

        return review
