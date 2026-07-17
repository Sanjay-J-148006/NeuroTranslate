"""Structured logging with Loguru."""

import sys
import io
from loguru import logger
from config import settings


def setup_logger():
    logger.remove()  # Remove default handler

    fmt = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} - "
        "{message}"
    )

    # Console handler — force UTF-8 so special chars (→, arrows) don't crash on Windows cp1252
    stdout_utf8 = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    logger.add(stdout_utf8, format=fmt, level="DEBUG" if settings.DEBUG else "INFO", colorize=False)

    # File handler — UTF-8 encoding
    logger.add(
        "logs/neurotranslate_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="7 days",
        format=fmt,
        level="DEBUG",
        enqueue=True,
        encoding="utf-8",
    )

    return logger


app_logger = setup_logger()

