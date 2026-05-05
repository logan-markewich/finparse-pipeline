from fastapi import APIRouter, HTTPException

from app.schemas import ExtractionRequest, ExtractionResponse
from app.services import extractions as extractions_service

router = APIRouter()


@router.post(
    "/documents/{document_id}/extract",
    response_model=ExtractionResponse,
)
async def create_extraction(document_id: int, request: ExtractionRequest):
    """Start a structured extraction job for a parsed document."""
    try:
        extraction = await extractions_service.create_extraction(document_id, request.schema_name)
    except extractions_service.DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="Document not found") from None
    except extractions_service.DocumentNotParsedError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    return ExtractionResponse.from_orm_with_json(extraction)


@router.get("/{extraction_id}", response_model=ExtractionResponse)
async def get_extraction(extraction_id: int):
    """Get an extraction by ID."""
    extraction = await extractions_service.get_extraction(extraction_id)
    if not extraction:
        raise HTTPException(status_code=404, detail="Extraction not found")
    return ExtractionResponse.from_orm_with_json(extraction)


@router.get(
    "/documents/{document_id}",
    response_model=list[ExtractionResponse],
)
async def list_extractions_for_document(document_id: int):
    """List all extractions for a document."""
    results = await extractions_service.get_extractions_for_document(document_id)
    return [ExtractionResponse.from_orm_with_json(e) for e in results]
