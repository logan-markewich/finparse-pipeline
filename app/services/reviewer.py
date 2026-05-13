"""Review lifecycle service.

Orchestrates the human-in-the-loop review flow:
1. Create a review from completed extractions
2. Run cross-document analysis via LlamaParse extraction (underwriting_summary schema)
3. Present to a human reviewer for approval/rejection
"""

import json

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app import db
from app.models import Review, ReviewStatus


async def run_review_analysis(review_id: int) -> None:
    """Run cross-document analysis for a review using LlamaParse extraction.

    This function runs as a background job (called via the worker queue).

    This combines the extracted data from
    all linked extractions into a text document, uploads it to LlamaParse as
    a buffer, and runs extraction with the "underwriting_summary" schema.

    Steps to implement:
        1. Load the review and its linked extractions from the DB
        2. Set review status to "analyzing"
        3. For each linked extraction, load the Extraction record and collect
           its schema_name + extracted_data
        4. Format the extraction data into a text document (see _format_extractions_as_text)
        5. Upload the text as a buffer file to LlamaParse:
             file_obj = await client.files.create(
                 file=io.BytesIO(text.encode("utf-8")),
                 purpose="extract",
                 external_file_id="review_{review_id}.txt",
             )
        6. Submit an extraction job using the underwriting_summary schema
        7. Poll for completion and get the result
        8. Store the result: review.llm_summary = json.dumps(result)
        9. Set status to "ready_for_review"
    """
    extraction_links = []
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
        extraction_links = review.extraction_links or []
        await session.commit()

    try:
        # ------------------------------------------------------------------
        # TODO: Implement the review analysis flow
        #
        # 1. For each extraction link, load the Extraction record
        # 2. Collect {"schema_name": ..., "data": ...} for each extraction
        # 3. Format into text with _format_extractions_as_text()
        # 4. Upload the text buffer to LlamaParse (see docstring above)
        # 5. Submit an extraction job with the underwriting_summary schema
        # 6. Poll for completion
        # 7. Store: review.llm_summary = json.dumps(result)
        # 8. Set review.status = ReviewStatus.ready_for_review
        # ------------------------------------------------------------------
        raise NotImplementedError("Implement review analysis — see instructions above")

    except Exception as e:
        async with db.async_session() as session:
            review = await session.get(Review, review_id)
            review.status = ReviewStatus.pending
            review.error = str(e)
            await session.commit()

        raise


def _format_extractions_as_text(extractions_data: list[dict]) -> str:
    """Format extraction data into a readable text document for LlamaParse.

    This is provided for you — use it in run_review_analysis() to build
    the text that gets uploaded as a buffer file.
    """
    sections = []
    for i, ext in enumerate(extractions_data, 1):
        schema = ext["schema_name"]
        data = ext["data"]
        sections.append(f"--- Document {i}: {schema} ---")
        sections.append(json.dumps(data, indent=2))
        sections.append("")

    header = (
        "BORROWER FINANCIAL DOCUMENTS\n"
        "The following extracted data comes from a borrower's financial documents.\n"
        "Analyze for loan underwriting: verify income, total assets, calculate "
        "months of reserves, and flag any discrepancies.\n"
    )
    return header + "\n" + "\n".join(sections)
