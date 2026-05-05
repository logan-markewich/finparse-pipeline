"""Document CRUD service."""

import os

from sqlalchemy import select

from app import db
from app.config import settings
from app.models import Document, JobStatus
from app.services.parser import parse_document
from app.worker import enqueue


async def create_document(filename: str, content: bytes) -> Document:
    """Save a file to disk, create a DB record, and enqueue parsing."""
    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(content)

    async with db.async_session() as session:
        doc = Document(
            filename=filename,
            file_path=file_path,
            status=JobStatus.pending,
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

    await enqueue(parse_document, doc.id, file_path)
    return doc


async def get_all_documents() -> list[Document]:
    async with db.async_session() as session:
        result = await session.execute(select(Document).order_by(Document.created_at.desc()))
        return list(result.scalars().all())


async def get_document(document_id: int) -> Document | None:
    async with db.async_session() as session:
        return await session.get(Document, document_id)
