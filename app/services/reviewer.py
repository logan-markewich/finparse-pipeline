"""Review analysis service.

Runs cross-document analysis via LlamaParse extraction (underwriting_summary schema).
"""

import asyncio
import io
import json

from llama_cloud import AsyncLlamaCloud
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app import db
from app.config import settings
from app.extraction_schemas.underwriting_summary import UnderwritingSummary
from app.models import (
    Extraction,
    JobStatus,
    Review,
    ReviewStatus,
)


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
        # 1. For each extraction link, load the Extraction record
        extraction_data = []
        for link in extraction_links:
            async with db.async_session() as session:
                extraction = await session.get(Extraction, link.extraction_id)
                if not extraction:
                    raise Exception(f"Extraction {link.extraction_id} not found")
                if extraction.status != JobStatus.completed:
                    raise Exception(f"Extraction {link.extraction_id} not completed (status: {extraction.status.value})")

                # 2. Collect {"schema_name": ..., "data": ...} for each extraction
                extraction_data.append({
                    "schema_name": extraction.schema_name,
                    "data": json.loads(extraction.extracted_data) if extraction.extracted_data else None,
                })

        # 3. Format into text with _format_extractions_as_text()
        text = _format_extractions_as_text(extraction_data)

        # 4. Upload the text buffer to LlamaParse (see docstring above)
        client = AsyncLlamaCloud(api_key=settings.llama_cloud_api_key)
        file_obj = await client.files.create(
            file=(f"review_{review_id}.txt", io.BytesIO(text.encode("utf-8"))),
            purpose="extract",
        )

        # 5. Submit an extraction job with the underwriting_summary schema
        job = await client.extract.create(
            file_input=file_obj.id,
            configuration={
                "data_schema": UnderwritingSummary.model_json_schema(),
                "tier": "agentic",
                "system_prompt": (
                    "You are a senior mortgage underwriter reviewing a borrower's financial documents. "
                    "Your job is to catch every risk factor and inconsistency across documents. "
                    "Be skeptical and thorough. Use standard underwriting guidelines to identify "
                    "discrepancies that could indicate undisclosed debt, mandatory obligations, "
                    "or other financial risks, and flag/report them accordingly."
                ),
            },
        )

        # 6. Poll for completion
        result = await client.extract.get(job.id)
        while result.status not in ["COMPLETED", "FAILED", "CANCELED"]:
            await asyncio.sleep(5)
            result = await client.extract.get(job.id)

        if result.status != "COMPLETED":
            raise Exception(
                f"Review analysis job failed: {result.status} -> {result.error_message}"
            )

        # 7. Store: review.llm_summary = json.dumps(result)
        # 8. Set review.status = ReviewStatus.ready_for_review
        async with db.async_session() as session:
            review = await session.get(Review, review_id)
            review.llm_summary = json.dumps(result.extract_result)
            review.status = ReviewStatus.ready_for_review

            await session.commit()

    except Exception as e:
        async with db.async_session() as session:
            review = await session.get(Review, review_id)
            if review:
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
        sections.append(f"<document idx={i} schema={schema}>\n")
        sections.append(json.dumps(data, indent=2))
        sections.append("\n</document>\n")

    header = (
        "BORROWER FINANCIAL DOCUMENTS\n"
        "The following extracted data comes from a borrower's financial documents.\n"
        "Analyze for loan underwriting: verify income, total assets, calculate "
        "months of reserves, and flag any discrepancies.\n\n"
        "IMPORTANT — thoroughly check for ALL of the following and report each as a discrepancy:\n"
        "- Name mismatches between documents (even minor spelling differences)\n"
        "- Address mismatches between documents\n"
        "- Wage garnishments, child support, or IRS levies on pay stubs (these are HIGH severity — "
        "they indicate undisclosed debts or mandatory obligations that affect debt-to-income)\n"
        "- Asset balances or large deposits that are inconsistent with the borrower's stated income\n"
        "- Portfolio concentrated heavily in a single security (risky collateral)\n"
        "- Income that doesn't annualize cleanly (may indicate recent job change or rate change)\n"
        "- Overtime or bonus income that inflates gross pay beyond base salary\n"
        "Do NOT bury findings in 'notes' — every red flag must appear as a discrepancy entry.\n"
    )
    return header + "\n" + "\n".join(sections)
