"""
Language Detection — 100% Offline script-based detection using Unicode character ranges.
Highly optimized, fast, and does not require any internet downloads.
"""

from __future__ import annotations
import re
from utils.logger import app_logger


def detect_language(text: str) -> tuple[str, float]:
    """
    Detect language of text using Unicode script ranges (100% offline, zero latency).
    
    Returns:
        (language_code, confidence) — language_code is "ne" / "si" / "en"
    """
    if not text or not text.strip():
        return "en", 1.0

    # Count characters of different script families
    devanagari_chars = len(re.findall(r'[\u0900-\u097f]', text))
    sinhala_chars = len(re.findall(r'[\u0d80-\u0dff]', text))
    latin_chars = len(re.findall(r'[a-zA-Z]', text))

    total = devanagari_chars + sinhala_chars + latin_chars

    # If no readable chars of target scripts, count all non-whitespace chars
    if total == 0:
        cleaned = re.sub(r'\s', '', text)
        if not cleaned:
            return "en", 1.0
        total = len(cleaned)

    # Determine dominant script
    if devanagari_chars > sinhala_chars and devanagari_chars > latin_chars:
        conf = devanagari_chars / total
        return "ne", conf
    elif sinhala_chars > devanagari_chars and sinhala_chars > latin_chars:
        conf = sinhala_chars / total
        return "si", conf
    else:
        # Default to English
        # If there are devanagari or sinhala characters present, score accordingly
        if latin_chars > 0:
            conf = latin_chars / total
        else:
            conf = 1.0
        return "en", conf


def detect_dominant_language(blocks: list[str]) -> tuple[str, float]:
    """
    Detect the dominant language across multiple text blocks.
    Uses majority voting weighted by character counts.
    """
    if not blocks:
        return "en", 1.0

    lang_scores: dict[str, float] = {"ne": 0.0, "si": 0.0, "en": 0.0}

    for text in blocks:
        if not text.strip():
            continue
        lang, conf = detect_language(text)
        weight = conf * len(text)
        lang_scores[lang] = lang_scores.get(lang, 0.0) + weight

    dominant = max(lang_scores, key=lang_scores.get)
    total_weight = sum(lang_scores.values())
    dominant_conf = lang_scores[dominant] / total_weight if total_weight > 0 else 1.0

    app_logger.info(f"Dominant language detected (offline Unicode): {dominant} (conf={dominant_conf:.3f})")
    return dominant, min(dominant_conf, 1.0)
