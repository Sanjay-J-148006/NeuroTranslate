"""
Confidence Scorer — Weighted multi-signal confidence engine.

Weights (FINAL):
  Translation Quality  50%
  NER Preservation     20%
  Glossary Preservation 15%
  Language Detection   15%

Score 0–100:
  90–100 → High Confidence
  70–89  → Moderate Confidence
  <70    → Needs Human Review
"""

from __future__ import annotations
from config import settings
from utils.logger import app_logger


def compute_confidence(
    translation_confidence: float,   # 0.0–1.0 from translation model
    language_confidence: float,      # 0.0–1.0 from FastText
    ner_preservation_rate: float,    # 0.0–1.0
    glossary_preservation_rate: float,  # 0.0–1.0
) -> dict:
    """
    Compute the final confidence score and category.

    Returns:
        {
            "score": float (0–100),
            "level": "high" | "moderate" | "low",
            "breakdown": dict of per-signal scores
        }
    """
    # Clamp all inputs to [0, 1]
    tc  = max(0.0, min(1.0, translation_confidence))
    lc  = max(0.0, min(1.0, language_confidence))
    ner = max(0.0, min(1.0, ner_preservation_rate))
    gl  = max(0.0, min(1.0, glossary_preservation_rate))

    weighted = (
        tc  * settings.CONFIDENCE_WEIGHT_TRANSLATION +
        ner * settings.CONFIDENCE_WEIGHT_NER +
        gl  * settings.CONFIDENCE_WEIGHT_GLOSSARY +
        lc  * settings.CONFIDENCE_WEIGHT_LANGDETECT
    )
    score = round(weighted * 100, 2)

    if score >= settings.CONFIDENCE_HIGH_THRESHOLD:
        level = "high"
    elif score >= settings.CONFIDENCE_MODERATE_THRESHOLD:
        level = "moderate"
    else:
        level = "low"

    breakdown = {
        "translation_quality": round(tc * 100, 2),
        "language_detection":  round(lc * 100, 2),
        "ner_preservation":    round(ner * 100, 2),
        "glossary_preservation": round(gl * 100, 2),
        "weights": {
            "translation": settings.CONFIDENCE_WEIGHT_TRANSLATION,
            "ner": settings.CONFIDENCE_WEIGHT_NER,
            "glossary": settings.CONFIDENCE_WEIGHT_GLOSSARY,
            "language": settings.CONFIDENCE_WEIGHT_LANGDETECT,
        },
    }

    app_logger.info(f"Confidence score: {score:.1f} ({level}) | TC={tc:.2f} LC={lc:.2f} NER={ner:.2f} GL={gl:.2f}")

    return {"score": score, "level": level, "breakdown": breakdown}
