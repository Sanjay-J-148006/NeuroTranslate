"""
NeuroTranslate — Central Configuration
All settings loaded from environment variables with safe defaults.
"""

import os
import torch
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


BASE_DIR = Path(__file__).parent


class Settings(BaseSettings):
    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "NeuroTranslate"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ── Database ──────────────────────────────────────────────────────────────
    # SQLite (default, no server needed) — just a file next to backend/
    DATABASE_URL: str = "sqlite+aiosqlite:///./neurotranslate.db"
    DATABASE_SYNC_URL: str = "sqlite:///./neurotranslate.db"

    # ── File Upload ───────────────────────────────────────────────────────────
    UPLOAD_DIR: Path = BASE_DIR.parent / "uploads"
    MAX_FILE_SIZE_MB: int = 1024

    @property
    def MAX_FILE_SIZE_BYTES(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    ALLOWED_EXTENSIONS: set = {
        # Documents
        ".pdf", ".docx", ".txt", ".csv",
        # Images
        ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp",
        # Audio
        ".mp3", ".wav", ".m4a", ".ogg", ".flac",
        # Video (optional)
        ".mp4", ".avi", ".mov", ".mkv",
    }

    ALLOWED_MIME_TYPES: set = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/plain", "text/csv",
        "image/png", "image/jpeg", "image/tiff", "image/bmp", "image/webp",
        "audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4",
        "audio/ogg", "audio/flac", "audio/x-flac",
        "video/mp4", "video/x-msvideo", "video/quicktime", "video/x-matroska",
    }

    # ── Model Paths & Names ───────────────────────────────────────────────────
    # Nepali Translation
    INDICTRANS2_MODEL: str = "ai4bharat/indictrans2-indic-en-dist-200M"
    INDICTRANS2_SRC_LANG: str = "npi_Deva"   # Nepali (Devanagari)
    INDICTRANS2_TGT_LANG: str = "eng_Latn"   # English (Latin)

    # Sinhala & Nepali Translation (CTranslate2 optimized)
    NLLB_MODEL: str = "JustFrederik/nllb-200-distilled-600M-ct2-int8"
    NLLB_SRC_LANG: str = "sin_Sinh"          # Sinhala
    NLLB_TGT_LANG: str = "eng_Latn"          # English (Latin)

    # NER
    NER_MODEL: str = "Davlan/xlm-roberta-base-ner-hrl"

    # ASR (Whisper)
    WHISPER_MODEL_SIZE: str = "small"        # ~500MB, multilingual

    # ── Hugging Face ────────────────────────────────────────────────────────────
    HF_TOKEN: str = Field(default="")

    # ── Language Detection ────────────────────────────────────────────────────
    FASTTEXT_MODEL: str = "lid.176.bin"
    FASTTEXT_LOW_MEMORY: bool = False

    # Language codes that trigger translation
    SUPPORTED_SOURCE_LANGS: dict = {
        "ne": "nepali",
        "si": "sinhala",
        "en": "english",   # pass-through
    }

    # ── Confidence Engine Weights ─────────────────────────────────────────────
    CONFIDENCE_WEIGHT_TRANSLATION: float = 0.50
    CONFIDENCE_WEIGHT_NER: float = 0.20
    CONFIDENCE_WEIGHT_GLOSSARY: float = 0.15
    CONFIDENCE_WEIGHT_LANGDETECT: float = 0.15

    CONFIDENCE_HIGH_THRESHOLD: float = 90.0
    CONFIDENCE_MODERATE_THRESHOLD: float = 70.0

    # ── Glossary ─────────────────────────────────────────────────────────────
    GLOSSARY_PATH: Path = BASE_DIR / "data" / "glossary.json"

    # ── Export ────────────────────────────────────────────────────────────────
    EXPORT_DIR: Path = BASE_DIR.parent / "exports"

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: list = [
        "http://localhost:5173",   # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    class Config:
        env_file = BASE_DIR.parent / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton settings instance
settings = Settings()

# ── Device Detection ──────────────────────────────────────────────────────────
def get_device() -> str:
    """Auto-detect CUDA; fall back to CPU."""
    if torch.cuda.is_available():
        device = "cuda"
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"[NeuroTranslate] GPU detected: {gpu_name} ({vram_gb:.1f} GB VRAM) — using CUDA")
    else:
        device = "cpu"
        print("[NeuroTranslate] No GPU detected — using CPU (expect slower inference)")
    return device


DEVICE = get_device()

# Ensure critical directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# Set HF_TOKEN in environment so all Hugging Face hub calls use it automatically
if settings.HF_TOKEN:
    os.environ["HF_TOKEN"] = settings.HF_TOKEN

