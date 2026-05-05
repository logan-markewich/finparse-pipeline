"""Review lifecycle service.

Orchestrates the human-in-the-loop review flow:
1. Create a review from completed extractions
2. Run LLM analysis to produce an underwriting summary
3. Present to a human reviewer for approval/rejection
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import async_session
from app.models import (
    Review,
    ReviewDecision,
    ReviewStatus,
)


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
    async with async_session() as db:
        result = await db.execute(
            select(Review)
            .options(selectinload(Review.extraction_links))
            .where(Review.id == review_id)
        )
        review = result.scalar_one_or_none()
        if not review:
            return

        review.status = ReviewStatus.analyzing
        await db.commit()

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

            await db.commit()

        except Exception as e:
            review.status = ReviewStatus.pending
            review.error = str(e)
            await db.commit()
            raise


async def update_review_decision(
    review: Review,
    decision: ReviewDecision,
    reviewer_notes: str | None,
    db: AsyncSession,
) -> None:
    """Record the human reviewer's decision.

    This one is simple — just update the fields and commit.
    """
    # ------------------------------------------------------------------
    # TODO: Implement the decision update
    #
    # 1. Set review.decision = decision
    # 2. Set review.reviewer_notes = reviewer_notes
    # 3. Set review.status to approved or rejected based on the decision
    # 4. Commit
    # ------------------------------------------------------------------
    raise NotImplementedError("Implement review decision update — see instructions above")
