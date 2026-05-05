"""Review lifecycle service.

Orchestrates the human-in-the-loop review flow:
1. Create a review from completed extractions
2. Run LLM analysis to produce an underwriting summary
3. Present to a human reviewer for approval/rejection
"""

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
    """Validate extractions, create a review, and enqueue LLM analysis."""
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

        # ------------------------------------------------------------------
        # TODO: Implement the decision update
        #
        # 1. Set review.decision = decision
        # 2. Set review.reviewer_notes = reviewer_notes
        # 3. Set review.status to approved or rejected based on the decision
        # 4. Commit
        # ------------------------------------------------------------------
        raise NotImplementedError("Implement review decision update — see instructions above")


async def run_review_analysis(review_id: int) -> None:
    """Run LLM analysis for a review and update its status.

    This function runs as a background job (called via the worker queue).

    Steps to implement:
        1. Load the review and its linked extractions from the DB
        2. Set review status to "analyzing"
        3. Collect the extracted data from each linked extraction
        4. Call analyze_extractions() with the data
        5. Store the LLM summary on the review record
        6. Set status to "ready_for_review"
    """
    async with db.async_session() as session:
        result = await session.execute(
            select(Review)
            .options(selectinload(Review.extraction_links))
            .where(Review.id == review_id)
        )
        review = result.scalar_one_or_none()
        if not review:
            return

        review.status = ReviewStatus.analyzing
        await session.commit()

        try:
            # ------------------------------------------------------------------
            # TODO: Implement the review analysis flow
            #
            # 1. For each extraction link, load the Extraction record
            # 2. Build a list of {"schema_name": ..., "data": ...} dicts
            #    (parse the JSON from extraction.extracted_data)
            # 3. Call analyze_extractions(extractions_data)
            # 4. Store the result: review.llm_summary = json.dumps(summary)
            # 5. Set review.status = ReviewStatus.ready_for_review
            # ------------------------------------------------------------------
            raise NotImplementedError("Implement review analysis — see instructions above")

            await session.commit()

        except Exception as e:
            review.status = ReviewStatus.pending
            review.error = str(e)
            await session.commit()
            raise
