"""
NER Engine — XLM-RoBERTa Base NER HRL.
Model: Davlan/xlm-roberta-base-ner-hrl
Entities: PER, ORG, LOC, DATE (+ MISC catch-all)
"""

from __future__ import annotations
from typing import List
from utils.logger import app_logger

def _get_ner_pipeline():
    """Lazy-load the NER pipeline (~1.1 GB) using model_manager."""
    from pipeline.model_manager import get_ner
    return get_ner()


def unload_ner_model():
    """Unload NER model from RAM."""
    from pipeline.model_manager import unload_ner
    unload_ner()


def extract_entities(text: str) -> List[dict]:
    """
    Extract named entities from text.

    Returns list of:
        {"text": str, "label": str, "start": int, "end": int, "score": float}
    """
    if not text or len(text.strip()) < 3:
        return []

    try:
        ner = _get_ner_pipeline()
        results = ner(text[:1024])   # Truncate to avoid OOM on very long texts

        entities = []
        for entity in results:
            entities.append({
                "text":  entity["word"],
                "label": entity["entity_group"],    # PER / ORG / LOC / MISC
                "start": entity["start"],
                "end":   entity["end"],
                "score": round(float(entity["score"]), 4),
            })

        app_logger.debug(f"NER found {len(entities)} entities in {len(text)} chars")
        return entities

    except Exception as e:
        app_logger.error(f"NER extraction failed: {e}")
        return []


def compute_ner_preservation_rate(
    source_entities: List[dict],
    translated_entities: List[dict],
) -> float:
    """
    Compare entity texts from source and translated text.
    Returns ratio of source entities that appear (verbatim or close match)
    in the translation.
    """
    if not source_entities:
        return 1.0   # Nothing to preserve

    source_texts = {e["text"].lower() for e in source_entities}
    translated_texts = {e["text"].lower() for e in translated_entities}

    preserved = source_texts & translated_texts
    rate = len(preserved) / len(source_texts)
    app_logger.debug(f"NER preservation: {len(preserved)}/{len(source_texts)} = {rate:.2f}")
    return rate


# ── PII Redaction Labels ──────────────────────────────────────────────────────

_PII_LABELS = {
    "PER":  "PERSON",
    "ORG":  "ORGANIZATION",
    "LOC":  "LOCATION",
    "MISC": "ENTITY",
    "DATE": "DATE",
}


def anonymize_text(text: str, entities: List[dict] | None = None) -> tuple[str, List[dict]]:
    """
    Replace PII entities in text with redaction placeholders.

    Args:
        text: The text to anonymize.
        entities: Pre-extracted entities (optional). If None, we extract them.

    Returns:
        (anonymized_text, entities_used)
    """
    if not text or len(text.strip()) < 3:
        return text, []

    if entities is None:
        entities = extract_entities(text)

    if not entities:
        return text, entities

    # Sort entities by start position in reverse order so we can replace without shifting indices
    sorted_entities = sorted(entities, key=lambda e: e.get("start", 0), reverse=True)

    # Track counters per label type for unique numbering
    label_counters: dict[str, int] = {}
    # Track text->placeholder mapping to reuse same placeholder for same entity text
    text_to_placeholder: dict[str, str] = {}

    anonymized = text
    for ent in sorted_entities:
        entity_text = ent.get("text", "")
        label = ent.get("label", "MISC")
        start = ent.get("start", 0)
        end = ent.get("end", 0)

        if not entity_text or start >= end:
            continue

        # Reuse placeholder if same entity text was already assigned one
        if entity_text.lower() in text_to_placeholder:
            placeholder = text_to_placeholder[entity_text.lower()]
        else:
            pii_label = _PII_LABELS.get(label, "ENTITY")
            label_counters[pii_label] = label_counters.get(pii_label, 0) + 1
            placeholder = f"[{pii_label}_{label_counters[pii_label]}]"
            text_to_placeholder[entity_text.lower()] = placeholder

        anonymized = anonymized[:start] + placeholder + anonymized[end:]

    app_logger.info(f"PII anonymization: {len(sorted_entities)} entities redacted")
    return anonymized, entities
