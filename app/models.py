import datetime
import enum

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ---------- Enums ----------


class JobStatus(enum.StrEnum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class ReviewStatus(enum.StrEnum):
    pending = "pending"
    analyzing = "analyzing"
    ready_for_review = "ready_for_review"
    approved = "approved"
    rejected = "rejected"


class ReviewDecision(enum.StrEnum):
    approved = "approved"
    rejected = "rejected"


# ---------- Models ----------


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.pending)
    parsed_markdown: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    extractions: Mapped[list["Extraction"]] = relationship(back_populates="document")


class Extraction(Base):
    __tablename__ = "extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    schema_name: Mapped[str] = mapped_column(String, nullable=False)
    extracted_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.pending)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    document: Mapped["Document"] = relationship(back_populates="extractions")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), default=ReviewStatus.pending)
    llm_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    reviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision: Mapped[ReviewDecision | None] = mapped_column(Enum(ReviewDecision), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    extraction_links: Mapped[list["ReviewExtraction"]] = relationship(back_populates="review")


class ReviewExtraction(Base):
    """Join table linking reviews to extractions."""

    __tablename__ = "review_extractions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), nullable=False)
    extraction_id: Mapped[int] = mapped_column(ForeignKey("extractions.id"), nullable=False)

    review: Mapped["Review"] = relationship(back_populates="extraction_links")
    extraction: Mapped["Extraction"] = relationship()
