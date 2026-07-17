"""File upload validation, MIME detection, and temp storage management."""

import os
import uuid
import mimetypes
from pathlib import Path
from fastapi import UploadFile, HTTPException
from config import settings
from utils.logger import app_logger


def get_file_extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def detect_file_type_category(filename: str) -> str:
    """Return coarse category: pdf / image / docx / txt / audio / video."""
    ext = get_file_extension(filename)
    mapping = {
        ".pdf": "pdf",
        ".docx": "docx",
        ".txt": "txt", ".csv": "txt",
        ".png": "image", ".jpg": "image", ".jpeg": "image",
        ".tiff": "image", ".tif": "image", ".bmp": "image", ".webp": "image",
        ".mp3": "audio", ".wav": "audio", ".m4a": "audio",
        ".ogg": "audio", ".flac": "audio",
        ".mp4": "video", ".avi": "video", ".mov": "video", ".mkv": "video",
    }
    return mapping.get(ext, "unknown")


async def validate_and_save_upload(file: UploadFile) -> tuple[Path, str]:
    """
    Validate upload and save to temp directory.

    Returns:
        (saved_path, file_type_category)

    Raises:
        HTTPException on validation failure.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    ext = get_file_extension(file.filename)
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not supported. Allowed: {sorted(settings.ALLOWED_EXTENSIONS)}",
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if file_size > settings.MAX_FILE_SIZE_BYTES:
        size_mb = file_size / 1024 / 1024
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {size_mb:.1f} MB. Maximum allowed: {settings.MAX_FILE_SIZE_MB} MB.",
        )

    # Save to upload directory with unique name
    unique_name = f"{uuid.uuid4()}{ext}"
    save_path = settings.UPLOAD_DIR / unique_name
    save_path.write_bytes(content)

    file_type = detect_file_type_category(file.filename)
    app_logger.info(f"Saved upload: {file.filename} → {save_path} ({file_size/1024:.1f} KB, type={file_type})")

    return save_path, file_type


def cleanup_file(path: Path) -> None:
    """Delete a temp file safely."""
    try:
        if path and path.exists():
            path.unlink()
            app_logger.debug(f"Cleaned up temp file: {path}")
    except Exception as e:
        app_logger.warning(f"Could not delete temp file {path}: {e}")
