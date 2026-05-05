import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models import Document, JobStatus
from app.schemas import DocumentDetailResponse, DocumentResponse
from app.services.parser import parse_document
from app.worker import enqueue

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile, db: AsyncSession = Depends(get_db)):
    """Upload a financial document (PDF) and kick off parsing."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    os.makedirs(settings.upload_dir, exist_ok=True)
    file_path = os.path.join(settings.upload_dir, file.filename)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        filename=file.filename,
        file_path=file_path,
        status=JobStatus.pending,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    await enqueue(parse_document, doc.id, file_path)

    return doc


@router.get("/", response_model=list[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)):
    """List all uploaded documents."""
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return result.scalars().all()


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(document_id: int, db: AsyncSession = Depends(get_db)):
    """Get a document by ID, including parsed markdown if available."""
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
