"""Glossary router — CRUD API for terminology management."""

import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import settings
from utils.logger import app_logger

router = APIRouter(prefix="/api/glossary", tags=["glossary"])

GLOSSARY_PATH = Path(settings.GLOSSARY_PATH)


def _read_glossary() -> dict:
    if not GLOSSARY_PATH.exists():
        return {"ne": {}, "si": {}}
    with open(GLOSSARY_PATH, encoding="utf-8") as f:
        return json.load(f)


def _write_glossary(data: dict):
    GLOSSARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GLOSSARY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class GlossaryTermRequest(BaseModel):
    language: str          # "ne" or "si"
    source_term: str       # e.g. "कार्यालय"
    target_term: str       # e.g. "Ministry Office"


@router.get("")
async def get_glossary():
    """Return full glossary dictionary."""
    return _read_glossary()


@router.post("")
async def add_glossary_term(req: GlossaryTermRequest):
    """Add or update a glossary term."""
    data = _read_glossary()
    lang = req.language
    if lang not in data:
        data[lang] = {}
    data[lang][req.source_term] = req.target_term
    _write_glossary(data)

    # Reload glossary in the engine
    from pipeline.glossary_engine import _load_glossary, _GLOSSARY
    import pipeline.glossary_engine as ge
    ge._GLOSSARY = _load_glossary()

    app_logger.info(f"Glossary: added '{req.source_term}' -> '{req.target_term}' ({lang})")
    return {"status": "ok", "message": f"Term added: {req.source_term} -> {req.target_term}"}


@router.delete("/{language}/{source_term}")
async def delete_glossary_term(language: str, source_term: str):
    """Remove a glossary term."""
    data = _read_glossary()
    if language not in data or source_term not in data[language]:
        raise HTTPException(status_code=404, detail=f"Term '{source_term}' not found in '{language}' glossary.")
    
    del data[language][source_term]
    _write_glossary(data)

    # Reload glossary in the engine
    import pipeline.glossary_engine as ge
    ge._GLOSSARY = ge._load_glossary()

    app_logger.info(f"Glossary: removed '{source_term}' from {language}")
    return {"status": "ok", "message": f"Term '{source_term}' removed."}
