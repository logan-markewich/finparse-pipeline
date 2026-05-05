from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.models import Document, Extraction, JobStatus
from app.schemas import ExtractionRequest, ExtractionResponse
from app.services.extractor import extract_from_document
from app.worker import enqueue

router = APIRouter()


@router.post(
    "/documents/{document_id}/extract",
    response_model=ExtractionResponse,
)
async def create_extraction(
    document_id: int,
    request: ExtractionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Start a structured extraction job for a parsed document."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != JobStatus.completed:
        raise HTTPException(
            status_code=400,
            detail=f"Document must be parsed first (current status: {doc.status.value})",
        )

    extraction = Extraction(
        document_id=document_id,
        schema_name=request.schema_name,
        status=JobStatus.pending,
    )
    db.add(extraction)
    await db.commit()
    await db.refresh(extraction)

    await enqueue(extract_from_document, extraction.id, document_id, request.schema_name)

    return ExtractionResponse.from_orm_with_json(extraction)


@router.get("/{extraction_id}", response_model=ExtractionResponse)
async def get_extraction(extraction_id: int, db: AsyncSession = Depends(get_db)):
    """Get an extraction by ID."""
    extraction = await db.get(Extraction, extraction_id)
    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")
    return ExtractionResponse.from_orm_with_json(extraction)


@router.get(
    "/documents/{document_id}",
    response_model=list[ExtractionResponse],
)
async def list_extractions_for_document(document_id: int, db: AsyncSession = Depends(get_db)):
    """List all extractions for a document."""
    result = await db.execute(
        select(Extraction)
        .where(Extraction.document_id == document_id)
        .order_by(Extraction.created_at.desc())
    )
    return [ExtractionResponse.from_orm_with_json(e) for e in result.scalars().all()]
