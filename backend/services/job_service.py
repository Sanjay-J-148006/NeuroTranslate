"""Job CRUD service — PostgreSQL via SQLAlchemy async."""

from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import TranslationJob, JobStatus, ConfidenceLevel
from utils.logger import app_logger


async def create_job(
    db: AsyncSession,
    job_id: str,
    filename: str,
    file_type: str,
    file_size: int,
) -> TranslationJob:
    job = TranslationJob(
        id=job_id,
        status=JobStatus.PENDING,
        original_filename=filename,
        file_type=file_type,
        file_size_bytes=file_size,
    )
    db.add(job)
    await db.flush()
    app_logger.info(f"Created job {job_id} for '{filename}'")
    return job


async def get_job(db: AsyncSession, job_id: str) -> Optional[TranslationJob]:
    result = await db.execute(select(TranslationJob).where(TranslationJob.id == job_id))
    return result.scalar_one_or_none()


async def update_job_status(
    db: AsyncSession,
    job_id: str,
    status: JobStatus,
    **kwargs,
) -> None:
    job = await get_job(db, job_id)
    if not job:
        app_logger.warning(f"Job {job_id} not found for status update")
        return

    job.status = status
    job.updated_at = datetime.utcnow()
    for key, value in kwargs.items():
        if hasattr(job, key):
            setattr(job, key, value)

    await db.flush()
    app_logger.debug(f"Job {job_id} status → {status}")


async def mark_job_completed(
    db: AsyncSession,
    job_id: str,
    result: dict,
    processing_time: float,
) -> None:
    """Persist the full pipeline result."""
    confidence = result.get("confidence_score", 0.0)
    if confidence >= 90:
        conf_level = ConfidenceLevel.HIGH
    elif confidence >= 70:
        conf_level = ConfidenceLevel.MODERATE
    else:
        conf_level = ConfidenceLevel.LOW

    await update_job_status(
        db, job_id,
        status=JobStatus.COMPLETED,
        detected_language=result.get("detected_language"),
        language_confidence=result.get("language_confidence"),
        source_text=result.get("source_text"),
        translated_text=result.get("translated_text"),
        translation_model=result.get("translation_model"),
        ner_entities=result.get("ner_entities"),
        ner_preservation_rate=result.get("ner_preservation_rate"),
        glossary_matches=result.get("glossary_matches"),
        glossary_preservation_rate=result.get("glossary_preservation_rate"),
        sentence_pairs=result.get("sentence_pairs"),
        confidence_score=confidence,
        confidence_level=conf_level,
        export_pdf_path=result.get("export_pdf_path"),
        export_docx_path=result.get("export_docx_path"),
        export_txt_path=result.get("export_txt_path"),
        processing_time_seconds=processing_time,
    )


async def mark_job_failed(db: AsyncSession, job_id: str, error: str) -> None:
    await update_job_status(
        db, job_id,
        status=JobStatus.FAILED,
        error_message=error[:2000],
    )
