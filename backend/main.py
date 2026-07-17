"""
NeuroTranslate — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings, DEVICE
from database.connection import init_db
from routers import translate, jobs, download, glossary
from utils.logger import app_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    app_logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    app_logger.info(f"Device: {DEVICE}")
    app_logger.info(f"Upload dir: {settings.UPLOAD_DIR}")
    app_logger.info(f"Export dir: {settings.EXPORT_DIR}")

    # Initialise database tables
    await init_db()
    app_logger.info("Database initialised.")

    yield  # App runs here

    app_logger.info(f"{settings.APP_NAME} shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Multilingual AI Translation Pipeline — "
        "Nepali & Sinhala to English with OCR, NER, Glossary, and Confidence Scoring."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(translate.router)
app.include_router(jobs.router)
app.include_router(download.router)
app.include_router(glossary.router)


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check():
    return JSONResponse({
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "device": DEVICE,
    })


@app.get("/", tags=["root"])
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}. See /docs for API reference."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
