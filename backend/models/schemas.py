"""Pydantic request/response schemas for NeuroTranslate API."""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ── NER Entity ────────────────────────────────────────────────────────────────

class NEREntity(BaseModel):
    text: str
    label: str          # PER, ORG, LOC, DATE, EVENT
    start: int
    end: int
    score: float


# ── Glossary Match ────────────────────────────────────────────────────────────

class GlossaryMatch(BaseModel):
    original_term: str
    replacement: str
    position: int


# ── Translation Result ────────────────────────────────────────────────────────

class TranslationBlock(BaseModel):
    block_index: int
    source_text: str
    translated_text: str
    detected_language: str
    language_confidence: float
    translation_model: str          # indictrans2 / nllb / passthrough
    entities: List[NEREntity] = []
    glossary_matches: List[GlossaryMatch] = []
    block_confidence: float


# ── Job Response ──────────────────────────────────────────────────────────────

class JobStatusResponse(BaseModel):
    job_id: str
    status: str                     # pending / processing / completed / failed
    file_name: str
    file_type: str
    detected_language: Optional[str] = None
    language_confidence: Optional[float] = None
    translation_model: Optional[str] = None
    confidence_score: Optional[float] = None
    confidence_level: Optional[str] = None     # high / moderate / low
    source_text: Optional[str] = None
    translated_text: Optional[str] = None
    ner_entities: Optional[List[NEREntity]] = None
    glossary_matches: Optional[List[GlossaryMatch]] = None
    ner_preservation_rate: Optional[float] = None
    glossary_preservation_rate: Optional[float] = None
    sentence_pairs: Optional[list] = None
    processing_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TranslateResponse(BaseModel):
    job_id: str
    status: str = "pending"
    message: str = "File uploaded. Processing started."


class DownloadResponse(BaseModel):
    job_id: str
    format: str
    download_url: str


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    device: str
    models_loaded: List[str]


class EditSentenceRequest(BaseModel):
    sentence_index: int
    new_translation: str
