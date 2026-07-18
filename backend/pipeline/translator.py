"""
Translation Engine — Robust offline translation using NLLB-200 CTranslate2.
  - Nepali  → NLLB-200 (npi_Deva)    [reliable, offline, no extra dependencies]
  - Sinhala → NLLB-200 (sin_Sinh)
  - English → pass-through

IndicTrans2 support is conditionally activated if IndicTransToolkit is installed.
  pip install git+https://github.com/VarunGumma/IndicTransToolkit

Smart Unicode script detection routes mixed-language sentences automatically.
Lazy-loading / smart-unloading via model_manager keeps RAM below 700 MB.
"""

from __future__ import annotations
import re
import gc
from typing import Optional
from utils.logger import app_logger
from config import settings, DEVICE


# ── NLLB language codes ────────────────────────────────────────────────────────
_NLLB_LANG_MAP = {
    "ne": "npi_Deva",   # Nepali  → Devanagari
    "si": "sin_Sinh",   # Sinhala → Sinhala script
}

# Detect if IndicTransToolkit is available for higher-quality Nepali translation
_INDICTRANS_AVAILABLE = False
try:
    from IndicTransToolkit import IndicProcessor as _IP
    _INDICTRANS_AVAILABLE = True
    app_logger.info("IndicTransToolkit detected — Nepali will use IndicTrans2.")
except ImportError:
    app_logger.info("IndicTransToolkit not installed — Nepali will use NLLB-200 (reliable offline mode).")


# ── NLLB-200 (CTranslate2) ─────────────────────────────────────────────────────

def _get_nllb():
    from pipeline.model_manager import get_nllb
    return get_nllb()


def _translate_batch_nllb(sentences: list[str], src_lang: str) -> list[str]:
    """Translate a list of sentences using NLLB-200 CTranslate2."""
    if not sentences:
        return []

    translator, tokenizer = _get_nllb()
    tokenizer.src_lang = src_lang
    tgt_lang = settings.NLLB_TGT_LANG  # "eng_Latn"

    source_tokens = []
    for s in sentences:
        tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(s))
        source_tokens.append(tokens)

    translated_sentences = []
    batch_size = 32

    for i in range(0, len(source_tokens), batch_size):
        batch = source_tokens[i:i + batch_size]
        results = translator.translate_batch(
            batch,
            target_prefix=[[tgt_lang]] * len(batch),
            beam_size=1   # Fastest on CPU
        )
        for res in results:
            target_tokens = res.hypotheses[0]
            decoded = tokenizer.decode(tokenizer.convert_tokens_to_ids(target_tokens))
            if decoded.startswith(tgt_lang):
                decoded = decoded[len(tgt_lang):].strip()
            translated_sentences.append(decoded)

    return translated_sentences


# ── IndicTrans2 (optional) ──────────────────────────────────────────────────────

def _translate_batch_indictrans2(sentences: list[str]) -> list[str]:
    """Translate Nepali using IndicTrans2 + IndicTransToolkit preprocessing."""
    from pipeline.model_manager import get_indictrans2
    import torch

    model, tokenizer = get_indictrans2()
    ip = _IP(inference=True)

    # Preprocess: normalize, transliterate, add language tags
    batch = ip.preprocess_batch(sentences, src_lang="npi_Deva", tgt_lang="eng_Latn")
    inputs = tokenizer(
        batch, padding="longest", truncation=True, max_length=256, return_tensors="pt"
    ).to(DEVICE)

    with torch.inference_mode():
        generated_tokens = model.generate(
            **inputs, use_cache=False, min_length=0, max_length=256, num_beams=1
        )

    # Decode and postprocess the full batch at once
    decoded = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
    postprocessed = ip.postprocess_batch(decoded, lang="eng_Latn")
    return [s.strip() for s in postprocessed]


# ── Sentence utilities ─────────────────────────────────────────────────────────

def _split_into_sentences(text: str) -> list[str]:
    """Split text into sentences on common punctuation."""
    sentences = re.split(r'([.?!।]\s*)', text)
    chunks = []
    for i in range(0, len(sentences), 2):
        chunk = sentences[i]
        if i + 1 < len(sentences):
            chunk += sentences[i + 1]
        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def _detect_sentence_language(sentence: str, fallback_lang: str) -> str:
    """Fast Unicode-range script detection: Devanagari → ne, Sinhala → si, else → fallback."""
    if re.search(r'[\u0900-\u097f]', sentence):
        return "ne"
    if re.search(r'[\u0d80-\u0dff]', sentence):
        return "si"
    if fallback_lang == "en" or not re.search(r'[^\x00-\x7f]', sentence):
        return "en"
    return fallback_lang


def _estimate_confidence(src: str, tgt: str) -> float:
    """Simple word-ratio confidence proxy."""
    src_words = max(len(src.split()), 1)
    tgt_words = max(len(tgt.split()), 1)
    ratio = tgt_words / src_words
    score = 1.0 - abs(1.0 - ratio) * 0.5
    return min(max(score, 0.4), 1.0)


# ── Public API ─────────────────────────────────────────────────────────────────

def translate_chunks(chunks: list[Any], language: str) -> list[Any]:
    """
    Translate a list of TranslationChunks in batch.
    Keeps track of order and applies script detection to each chunk text.
    """
    if not chunks:
        return []

    # ── Step 1: Bucket chunks by script / model ────────────────────────────
    ne_idx, ne_txt = [], []
    si_idx, si_txt = [], []
    en_idx, en_txt = [], []

    for i, chunk in enumerate(chunks):
        lang = _detect_sentence_language(chunk.text, language)
        if lang == "ne":
            ne_idx.append(i); ne_txt.append(chunk.text)
        elif lang == "si":
            si_idx.append(i); si_txt.append(chunk.text)
        else:
            en_idx.append(i); en_txt.append(chunk.text)

    # ── Step 2: Translate each bucket sequentially (never load 2 models at once)
    translated: list[str] = [""] * len(chunks)
    model_flags: list[str] = []

    if ne_txt:
        try:
            if _INDICTRANS_AVAILABLE:
                app_logger.info(f"Batch-translating {len(ne_txt)} Nepali chunks via IndicTrans2...")
                ne_out = _translate_batch_indictrans2(ne_txt)
                model_flags.append("indictrans2")
            else:
                app_logger.info(f"Batch-translating {len(ne_txt)} Nepali chunks via NLLB-200...")
                ne_out = _translate_batch_nllb(ne_txt, "npi_Deva")
                model_flags.append("nllb-200")
        except Exception as e:
            app_logger.exception("Nepali batch translation failed. Falling back to NLLB-200.")
            ne_out = _translate_batch_nllb(ne_txt, "npi_Deva")
            model_flags.append("nllb-200(fallback)")

        for i, out in zip(ne_idx, ne_out):
            translated[i] = out

    if si_txt:
        app_logger.info(f"Batch-translating {len(si_txt)} Sinhala chunks via NLLB-200...")
        si_out = _translate_batch_nllb(si_txt, "sin_Sinh")
        for i, out in zip(si_idx, si_out):
            translated[i] = out
        model_flags.append("nllb-200")

    for i, t in zip(en_idx, en_txt):
        translated[i] = t

    # ── Step 3: Merge back to chunks ──────────────────────────────────────────
    for chunk, trans in zip(chunks, translated):
        chunk.translation = trans

    return chunks


def translate(text: str, language: str) -> dict:
    """
    Translate text to English.

    Args:
        text:     Source text (may contain mixed Nepali + Sinhala paragraphs).
        language: Dominant/detected language code ("ne" | "si" | "en").

    Returns:
        {
            "translated_text":       str,
            "model_used":            str,
            "translation_confidence": float,
            "sentence_pairs":        list[dict]
        }
    """
    text = text.strip()
    if not text:
        return {"translated_text": "", "model_used": "passthrough",
                "translation_confidence": 1.0, "sentence_pairs": []}

    # ── Step 1: Split paragraphs ──────────────────────────────────────────────
    paragraphs = text.split("\n")
    flat_sentences: list[str] = []
    paragraph_sentence_counts: list[int] = []

    for para in paragraphs:
        if not para.strip():
            paragraph_sentence_counts.append(0)
            continue
        sents = _split_into_sentences(para)
        flat_sentences.extend(sents)
        paragraph_sentence_counts.append(len(sents))

    # ── Step 2: Bucket sentences by script / model ────────────────────────────
    ne_idx, ne_txt = [], []
    si_idx, si_txt = [], []
    en_idx, en_txt = [], []

    for i, sent in enumerate(flat_sentences):
        lang = _detect_sentence_language(sent, language)
        if lang == "ne":
            ne_idx.append(i); ne_txt.append(sent)
        elif lang == "si":
            si_idx.append(i); si_txt.append(sent)
        else:
            en_idx.append(i); en_txt.append(sent)

    # ── Step 3: Translate each bucket sequentially (never load 2 models at once)
    translated: list[str] = [""] * len(flat_sentences)
    model_flags: list[str] = []

    if ne_txt:
        try:
            if _INDICTRANS_AVAILABLE:
                app_logger.info(f"Translating {len(ne_txt)} Nepali sentences via IndicTrans2...")
                ne_out = _translate_batch_indictrans2(ne_txt)
                model_flags.append("indictrans2")
            else:
                app_logger.info(f"Translating {len(ne_txt)} Nepali sentences via NLLB-200...")
                ne_out = _translate_batch_nllb(ne_txt, "npi_Deva")
                model_flags.append("nllb-200")
        except Exception as e:
            app_logger.exception("Nepali translation failed. Falling back to NLLB-200.")
            ne_out = _translate_batch_nllb(ne_txt, "npi_Deva")
            model_flags.append("nllb-200(fallback)")

        for i, out in zip(ne_idx, ne_out):
            translated[i] = out

    if si_txt:
        app_logger.info(f"Translating {len(si_txt)} Sinhala sentences via NLLB-200...")
        si_out = _translate_batch_nllb(si_txt, "sin_Sinh")
        for i, out in zip(si_idx, si_out):
            translated[i] = out
        model_flags.append("nllb-200")

    for i, t in zip(en_idx, en_txt):
        translated[i] = t
    if not ne_txt and not si_txt:
        model_flags.append("passthrough")

    # ── Step 4: Build sentence pairs ──────────────────────────────────────────
    sentence_pairs = []
    for i, (src, tgt) in enumerate(zip(flat_sentences, translated)):
        conf = _estimate_confidence(src, tgt)
        sentence_pairs.append({"index": i, "source": src, "translated": tgt, "confidence": round(conf, 3)})

    # ── Step 5: Reconstruct paragraphs ────────────────────────────────────────
    translated_paras = []
    s_idx = 0
    for count in paragraph_sentence_counts:
        if count == 0:
            translated_paras.append("")
            continue
        translated_paras.append(" ".join(translated[s_idx: s_idx + count]))
        s_idx += count

    translated_text = "\n".join(translated_paras)
    conf = _estimate_confidence(text, translated_text)
    model_used = "+".join(dict.fromkeys(model_flags))  # deduplicate, preserve order

    return {
        "translated_text": translated_text,
        "model_used": model_used,
        "translation_confidence": conf,
        "sentence_pairs": sentence_pairs,
    }
