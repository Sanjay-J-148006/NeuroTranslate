"""ORM table definitions for NeuroTranslate (SQLite-compatible)."""

import uuid
from datetime import datetime
from sqlalchemy import String, Float, Text, DateTime, JSON, Enum as SAEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from database.connection import Base
import enum


class JobStatus(str, enum.Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"


class ConfidenceLevel(str, enum.Enum):
    HIGH     = "high"
    MODERATE = "moderate"
    LOW      = "low"


class TranslationJob(Base):
    __tablename__ = "translation_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(JobStatus), default=JobStatus.PENDING, index=True
    )

    # Input
    original_filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(20))           # pdf/image/docx/txt/audio/video
    file_size_bytes: Mapped[int] = mapped_column(default=0)

    # Detection
    detected_language: Mapped[str | None] = mapped_column(String(10))     # ne/si/en
    language_confidence: Mapped[float | None] = mapped_column(Float)

    # Translation
    source_text: Mapped[str | None] = mapped_column(Text)
    translated_text: Mapped[str | None] = mapped_column(Text)
    translation_model: Mapped[str | None] = mapped_column(String(100))    # indictrans2/nllb/passthrough

    # Sentence-level pairs for interactive editing and confidence highlighting
    sentence_pairs: Mapped[dict | None] = mapped_column(JSON)            # list of {source, translated, confidence}

    # PII anonymization
    anonymize_pii: Mapped[bool] = mapped_column(Boolean, default=False)

    # NER
    ner_entities: Mapped[dict | None] = mapped_column(JSON)              # list of entity dicts
    ner_preservation_rate: Mapped[float | None] = mapped_column(Float)

    # Glossary
    glossary_matches: Mapped[dict | None] = mapped_column(JSON)          # list of match dicts
    glossary_preservation_rate: Mapped[float | None] = mapped_column(Float)

    # Confidence
    confidence_score: Mapped[float | None] = mapped_column(Float)
    confidence_level: Mapped[ConfidenceLevel | None] = mapped_column(SAEnum(ConfidenceLevel))

    # Export
    export_pdf_path: Mapped[str | None] = mapped_column(String(500))
    export_docx_path: Mapped[str | None] = mapped_column(String(500))
    export_txt_path: Mapped[str | None] = mapped_column(String(500))

    # Metadata
    error_message: Mapped[str | None] = mapped_column(Text)
    processing_time_seconds: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
