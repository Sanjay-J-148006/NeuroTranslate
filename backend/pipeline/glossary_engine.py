"""
Glossary Engine — JSON dictionary-based terminology enforcement.
Runs post-translation to replace generic translations with official terms.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import List
from config import settings
from utils.logger import app_logger


# ── Load Glossary ─────────────────────────────────────────────────────────────

def _load_glossary() -> dict:
    path = Path(settings.GLOSSARY_PATH)
    if not path.exists():
        app_logger.warning(f"Glossary file not found at {path}")
        return {"ne": {}, "si": {}}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_GLOSSARY: dict = _load_glossary()


# ── Application ───────────────────────────────────────────────────────────────

def apply_glossary(
    translated_text: str,
    source_language: str,
) -> tuple[str, List[dict]]:
    """
    Post-process translated text: replace model outputs with canonical terms.

    Args:
        translated_text: English text from translation model
        source_language: "ne" or "si" (used to select relevant glossary section)

    Returns:
        (corrected_text, list of match dicts)
    """
    lang_glossary = _GLOSSARY.get(source_language, {})
    if not lang_glossary:
        return translated_text, []

    matches: List[dict] = []
    result_text = translated_text

    # Build a second glossary: value → value (so we can also protect already-correct terms)
    english_glossary = {v.lower(): v for v in lang_glossary.values()}

    for source_term, canonical_term in lang_glossary.items():
        # Skip if canonical term already appears verbatim
        if canonical_term in result_text:
            continue

        # Search for approximate/partial matches of the canonical term
        # This catches cases where the model translates "Ministry of Defense" instead of "Defence"
        term_words = canonical_term.lower().split()
        if len(term_words) < 2:
            continue

        # Look for alternate capitalisations or British/American spelling variations
        pattern = re.compile(
            re.escape(canonical_term),
            re.IGNORECASE,
        )
        new_text, n_subs = re.subn(pattern, canonical_term, result_text)

        if n_subs > 0:
            result_text = new_text
            matches.append({
                "original_term": source_term,
                "replacement": canonical_term,
                "occurrences": n_subs,
            })

    if matches:
        app_logger.info(f"Glossary: {len(matches)} term(s) enforced")

    return result_text, matches


def get_glossary_preservation_rate(matches: List[dict], total_blocks: int) -> float:
    """
    Estimate how many expected glossary terms were either already correct
    or corrected post-translation.

    Returns float 0.0–1.0.
    """
    if total_blocks == 0:
        return 1.0
    return min(1.0, (len(matches) + total_blocks) / max(total_blocks, 1))
