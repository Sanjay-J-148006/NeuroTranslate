"""Jobs router — GET /api/jobs/{job_id} + POST /api/jobs/{job_id}/edit"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from models.schemas import JobStatusResponse, EditSentenceRequest
from services.job_service import get_job
from utils.logger import app_logger

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Poll translation job status and results."""
    job = await get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    # Deserialize JSON fields for response
    ner_entities     = job.ner_entities or []
    glossary_matches = job.glossary_matches or []
    sentence_pairs   = job.sentence_pairs or []

    return JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        file_name=job.original_filename,
        file_type=job.file_type,
        detected_language=job.detected_language,
        language_confidence=job.language_confidence,
        translation_model=job.translation_model,
        confidence_score=job.confidence_score,
        confidence_level=job.confidence_level.value if job.confidence_level else None,
        source_text=job.source_text,
        translated_text=job.translated_text,
        ner_entities=ner_entities,
        glossary_matches=glossary_matches,
        ner_preservation_rate=job.ner_preservation_rate,
        glossary_preservation_rate=job.glossary_preservation_rate,
        sentence_pairs=sentence_pairs,
        processing_time_seconds=job.processing_time_seconds,
        error_message=job.error_message,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.post("/{job_id}/edit")
async def edit_sentence(job_id: str, req: EditSentenceRequest, db: AsyncSession = Depends(get_db)):
    """
    Edit a single translated sentence and rebuild the full translated text.
    Also regenerates export files.
    """
    job = await get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    pairs = job.sentence_pairs or []
    if req.sentence_index < 0 or req.sentence_index >= len(pairs):
        raise HTTPException(status_code=400, detail=f"Sentence index {req.sentence_index} out of range (0-{len(pairs)-1}).")

    # Update the specific sentence
    pairs[req.sentence_index]["translated"] = req.new_translation
    pairs[req.sentence_index]["confidence"] = 1.0  # User-edited = perfect confidence

    # Rebuild full translated text from sentence pairs
    rebuilt_text = "\n".join(p["translated"] for p in pairs)

    job.sentence_pairs = pairs
    job.translated_text = rebuilt_text
    await db.flush()

    # Regenerate exports in background
    try:
        from pipeline.export_engine import export_all
        result = {
            "source_text": job.source_text,
            "translated_text": rebuilt_text,
        }
        export_paths = export_all(job_id, result)
        job.export_pdf_path = export_paths.get("pdf")
        job.export_docx_path = export_paths.get("docx")
        job.export_txt_path = export_paths.get("txt")
        await db.flush()
    except Exception as e:
        app_logger.warning(f"Export regeneration failed for {job_id}: {e}")

    app_logger.info(f"Job {job_id}: sentence {req.sentence_index} edited by user")
    return {
        "status": "ok",
        "message": f"Sentence {req.sentence_index} updated.",
        "translated_text": rebuilt_text,
    }
