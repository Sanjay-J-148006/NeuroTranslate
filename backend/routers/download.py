"""Download router — GET /api/download/{job_id}/{format}"""

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from services.job_service import get_job

router = APIRouter(prefix="/api/download", tags=["download"])

MIME_MAP = {
    "pdf":  ("application/pdf", "translated.pdf"),
    "docx": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "translated.docx"),
    "txt":  ("text/plain; charset=utf-8", "translated.txt"),
}


@router.get("/{job_id}/{fmt}")
async def download_export(job_id: str, fmt: str, db: AsyncSession = Depends(get_db)):
    """Download the translated export file (pdf / docx / txt)."""
    fmt = fmt.lower()
    if fmt not in MIME_MAP:
        raise HTTPException(status_code=400, detail=f"Invalid format '{fmt}'. Choose: pdf, docx, txt")

    job = await get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.status.value != "completed":
        raise HTTPException(status_code=409, detail=f"Job is not completed yet. Current status: {job.status.value}")

    path_attr = f"export_{fmt}_path"
    file_path_str = getattr(job, path_attr, None)

    if not file_path_str:
        raise HTTPException(status_code=404, detail=f"Export file for format '{fmt}' not found.")

    file_path = Path(file_path_str)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file missing from disk.")

    media_type, filename = MIME_MAP[fmt]
    safe_filename = f"{job.original_filename.rsplit('.', 1)[0]}_{filename}"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=safe_filename,
    )
