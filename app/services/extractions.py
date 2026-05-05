"""Extraction CRUD service."""

from sqlalchemy import select

from app import db
from app.models import Document, Extraction, JobStatus
from app.services.extractor import extract_from_document
from app.worker import enqueue


class DocumentNotFoundError(Exception):
    pass


class DocumentNotParsedError(Exception):
    def __init__(self, status: str):
        self.status = status
        super().__init__(f"Document must be parsed first (current status: {status})")


async def create_extraction(document_id: int, schema_name: str) -> Extraction:
    """Validate the document, create an extraction record, and enqueue the job."""
    async with db.async_session() as session:
        doc = await session.get(Document, document_id)
        if not doc:
            raise DocumentNotFoundError
        if doc.status != JobStatus.completed:
            raise DocumentNotParsedError(doc.status.value)

        extraction = Extraction(
            document_id=document_id,
            schema_name=schema_name,
            status=JobStatus.pending,
        )
        session.add(extraction)
        await session.commit()
        await session.refresh(extraction)

    await enqueue(extract_from_document, extraction.id, document_id, schema_name)
    return extraction


async def get_extraction(extraction_id: int) -> Extraction | None:
    async with db.async_session() as session:
        return await session.get(Extraction, extraction_id)


async def get_extractions_for_document(document_id: int) -> list[Extraction]:
    async with db.async_session() as session:
        result = await session.execute(
            select(Extraction)
            .where(Extraction.document_id == document_id)
            .order_by(Extraction.created_at.desc())
        )
        return list(result.scalars().all())
