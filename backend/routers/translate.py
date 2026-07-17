"""Translation router — POST /api/translate"""

import uuid
import asyncio
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import JobStatus
from models.schemas import TranslateResponse
from services.job_service import create_job, mark_job_completed, mark_job_failed, update_job_status
from utils.file_handler import validate_and_save_upload
from utils.logger import app_logger

router = APIRouter(prefix="/api", tags=["translation"])


async def _run_pipeline_background(
    job_id: str,
    file_path: Path,
    file_type: str,
    file_size: int,
    db_session,
    enable_ner: bool,
):
    """Background task: run full pipeline and persist results."""
    try:
        await update_job_status(db_session, job_id, JobStatus.PROCESSING)

        # Run pipeline in thread pool (CPU-bound work, avoid blocking event loop)
        loop = asyncio.get_event_loop()
        from pipeline.orchestrator import run_pipeline
        result = await loop.run_in_executor(None, run_pipeline, file_path, file_type, enable_ner)

        if "error" in result:
            await mark_job_failed(db_session, job_id, result["error"])
            return

        # Export files
        from pipeline.export_engine import export_all
        export_paths = await loop.run_in_executor(None, export_all, job_id, result)
        result["export_pdf_path"]  = export_paths.get("pdf")
        result["export_docx_path"] = export_paths.get("docx")
        result["export_txt_path"]  = export_paths.get("txt")

        await mark_job_completed(db_session, job_id, result, result.get("processing_time_seconds", 0))
        app_logger.info(f"Job {job_id} completed successfully.")

    except Exception as e:
        app_logger.error(f"Job {job_id} pipeline error: {e}", exc_info=True)
        await mark_job_failed(db_session, job_id, str(e))
    finally:
        from utils.file_handler import cleanup_file
        cleanup_file(file_path)


from fastapi import Form

@router.post("/translate", response_model=TranslateResponse, status_code=202)
async def translate_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    enable_ner: bool = Form(True),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document, image, audio, or video file for translation.
    Returns a job_id immediately; poll /api/jobs/{job_id} for results.
    """
    # Validate & save upload
    saved_path, file_type = await validate_and_save_upload(file)
    file_size = saved_path.stat().st_size

    # Create DB job record
    job_id = str(uuid.uuid4())
    await create_job(db, job_id, file.filename or "unknown", file_type, file_size)

    # Schedule background processing
    background_tasks.add_task(
        _run_pipeline_background,
        job_id, saved_path, file_type, file_size, db, enable_ner,
    )

    app_logger.info(f"Job {job_id} queued for '{file.filename}' ({file_type}) with enable_ner={enable_ner}")
    return TranslateResponse(job_id=job_id, status="pending", message="File uploaded. Processing started.")
