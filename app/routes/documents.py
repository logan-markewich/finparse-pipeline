from fastapi import APIRouter, HTTPException, UploadFile

from app.schemas import DocumentDetailResponse, DocumentResponse
from app.services import documents as documents_service

router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile):
    """Upload a financial document (PDF) and kick off parsing."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    content = await file.read()
    doc = await documents_service.create_document(file.filename, content)
    return doc


@router.get("/", response_model=list[DocumentResponse])
async def list_documents():
    """List all uploaded documents."""
    return await documents_service.get_all_documents()


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(document_id: int):
    """Get a document by ID, including parsed markdown if available."""
    doc = await documents_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc
