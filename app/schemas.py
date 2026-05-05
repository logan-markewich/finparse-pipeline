"""Pydantic schemas for API request/response models."""

import datetime
import json

from pydantic import BaseModel

from app.models import JobStatus, ReviewDecision, ReviewStatus

# ---------- Documents ----------


class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: JobStatus
    error: str | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class DocumentDetailResponse(DocumentResponse):
    parsed_markdown: str | None = None


# ---------- Extractions ----------


class ExtractionRequest(BaseModel):
    schema_name: str  # "pay_stub" or "brokerage_statement"


class ExtractionResponse(BaseModel):
    id: int
    document_id: int
    schema_name: str
    status: JobStatus
    extracted_data: dict | list | None = None
    error: str | None = None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_json(cls, obj) -> "ExtractionResponse":
        data = None
        if obj.extracted_data:
            data = json.loads(obj.extracted_data)
        return cls(
            id=obj.id,
            document_id=obj.document_id,
            schema_name=obj.schema_name,
            status=obj.status,
            extracted_data=data,
            error=obj.error,
            created_at=obj.created_at,
        )


# ---------- Reviews ----------


class ReviewCreateRequest(BaseModel):
    extraction_ids: list[int]


class ReviewUpdateRequest(BaseModel):
    decision: ReviewDecision
    reviewer_notes: str | None = None


class ReviewResponse(BaseModel):
    id: int
    status: ReviewStatus
    llm_summary: dict | None = None
    reviewer_notes: str | None = None
    decision: ReviewDecision | None = None
    error: str | None = None
    extraction_ids: list[int] = []
    created_at: datetime.datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_json(cls, obj) -> "ReviewResponse":
        summary = None
        if obj.llm_summary:
            summary = json.loads(obj.llm_summary)
        extraction_ids = [link.extraction_id for link in obj.extraction_links]
        return cls(
            id=obj.id,
            status=obj.status,
            llm_summary=summary,
            reviewer_notes=obj.reviewer_notes,
            decision=obj.decision,
            error=obj.error,
            extraction_ids=extraction_ids,
            created_at=obj.created_at,
        )
