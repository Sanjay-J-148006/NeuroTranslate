"""
Pipeline Orchestrator — Master controller.
Chains all 8 stages:
  1. Document Parsing
  2. OCR (if needed)
  3. ASR (audio / video)
  4. Language Detection
  5. Translation (IndicTrans2 / NLLB-200)
  6. Glossary Enforcement
  7. NER Protection
  8. Confidence Scoring
  → Export (PDF / DOCX / TXT)
"""

from __future__ import annotations
import time
from pathlib import Path
from utils.logger import app_logger


def run_pipeline(file_path: str | Path, file_type: str, enable_ner: bool = True) -> dict:
    """
    Run the full translation pipeline with reassembly and fusion.
    """
    start_time = time.time()
    file_path = Path(file_path)

    app_logger.info(f"Pipeline START — file={file_path.name}, type={file_type}")

    # ── Stage 1: Parse / ASR ──────────────────────────────────────────────────
    source_text = ""
    detected_language_from_asr = None
    asr_language_confidence = 0.0

    if file_type in ("audio", "video"):
        # Route to ASR engine — it returns text + language
        from pipeline.asr_engine import process_audio
        from pipeline.document_parser import ParsedDocument, TextBlock
        
        asr_result = process_audio(file_path, file_type)
        source_text = asr_result["text"]
        detected_language_from_asr = asr_result.get("language")
        asr_language_confidence = asr_result.get("language_probability", 0.0)
        app_logger.info(f"ASR: '{detected_language_from_asr}' ({asr_language_confidence:.2f}), {len(source_text)} chars")
        
        # Create a mock ParsedDocument for the ASR text
        parsed = ParsedDocument(source_path=file_path, file_type=file_type)
        parsed.blocks.append(TextBlock(text=source_text, block_index=0, block_type="paragraph"))
    else:
        # Parse document
        from pipeline.document_parser import parse_document
        parsed = parse_document(file_path, file_type)

        # ── Stage 2: OCR ──────────────────────────────────────────────────────
        if parsed.needs_ocr:
            from pipeline.ocr_engine import apply_ocr_to_document
            parsed = apply_ocr_to_document(parsed)

    source_text = "\n\n".join(b.text for b in parsed.blocks if b.text.strip())

    if not source_text.strip():
        return {
            "error": "No text could be extracted from the uploaded file.",
            "source_text": "",
            "translated_text": "",
            "detected_language": "unknown",
        }

    # ── Stage 3: Language Detection ───────────────────────────────────────────
    if detected_language_from_asr:
        # Trust Whisper's detection; also run FastText as validation
        from pipeline.language_detector import detect_language
        fasttext_lang, fasttext_conf = detect_language(source_text[:500])
        detected_language = detected_language_from_asr
        language_confidence = asr_language_confidence
    else:
        from pipeline.language_detector import detect_dominant_language
        text_samples = source_text.split("\n\n")[:5]   # Check first 5 blocks
        detected_language, language_confidence = detect_dominant_language(text_samples)

    app_logger.info(f"Language: {detected_language} (conf={language_confidence:.3f})")

    # ── Stage 4: Translation & Reassembly ─────────────────────────────────────
    from pipeline.reassembly import assign_metadata, merge_translation_with_metadata, reconstruct_document
    from pipeline.translator import translate_chunks
    
    # 1. Assign metadata (sentence splitting + structural block tagging)
    chunks = assign_metadata(parsed)
    
    # 2. Batch translation of chunks
    chunks = translate_chunks(chunks, detected_language)
    
    # 3. Glossary enforcement at chunk level
    from pipeline.glossary_engine import apply_glossary, get_glossary_preservation_rate
    glossary_matches = []
    for chunk in chunks:
        if chunk.translation:
            chunk.translation, chunk_matches = apply_glossary(chunk.translation, detected_language)
            glossary_matches.extend(chunk_matches)
            
    glossary_preservation_rate = get_glossary_preservation_rate(
        glossary_matches, len(parsed.blocks)
    )
    
    # 4. Reconstruct document
    reconstructed_doc = reconstruct_document(chunks)
    
    # 5. Extract flat outputs for legacy confidence/metadata metrics
    translated_text = "\n\n".join(p.translated_text for p in reconstructed_doc.all_paragraphs)
    
    # Calculate translation models used and confidence score
    from pipeline.translator import _estimate_confidence
    translation_confidence = _estimate_confidence(source_text, translated_text)
    
    # Extract unique models used based on sentence detection
    model_flags = []
    for chunk in chunks:
        from pipeline.translator import _detect_sentence_language, _INDICTRANS_AVAILABLE
        lang = _detect_sentence_language(chunk.text, detected_language)
        if lang == "ne":
            model_flags.append("indictrans2" if _INDICTRANS_AVAILABLE else "nllb-200")
        elif lang == "si":
            model_flags.append("nllb-200")
        else:
            model_flags.append("passthrough")
    model_used = "+".join(dict.fromkeys(model_flags))
    
    # Build sentence pairs list
    sentence_pairs = []
    for chunk in chunks:
        conf = _estimate_confidence(chunk.text, chunk.translation)
        sentence_pairs.append({
            "index": chunk.id,
            "source": chunk.text,
            "translated": chunk.translation,
            "confidence": round(conf, 3)
        })

    # ── Stage 6: NER ─────────────────────────────────────────────────────────
    if enable_ner:
        from pipeline.ner_engine import extract_entities, compute_ner_preservation_rate, unload_ner_model
        source_entities     = extract_entities(source_text[:1024])
        translated_entities = extract_entities(translated_text[:1024])
        # Immediately unload the 1.1GB NER model to free memory
        unload_ner_model()
        ner_preservation_rate = compute_ner_preservation_rate(source_entities, translated_entities)
    else:
        app_logger.info("NER model skipped per request (running in fast/low-RAM mode).")
        source_entities = []
        translated_entities = []
        ner_preservation_rate = 1.0

    # ── Stage 7: Confidence Score ─────────────────────────────────────────────
    from pipeline.confidence_scorer import compute_confidence
    confidence_result = compute_confidence(
        translation_confidence=translation_confidence,
        language_confidence=language_confidence,
        ner_preservation_rate=ner_preservation_rate,
        glossary_preservation_rate=glossary_preservation_rate,
    )

    processing_time = round(time.time() - start_time, 2)
    app_logger.info(
        f"Pipeline COMPLETE in {processing_time}s | "
        f"lang={detected_language} | model={model_used} | "
        f"confidence={confidence_result['score']:.1f} ({confidence_result['level']})"
    )

    return {
        "source_text": source_text,
        "translated_text": translated_text,
        "detected_language": detected_language,
        "language_confidence": round(language_confidence, 4),
        "translation_model": model_used,
        "translation_confidence": round(translation_confidence, 4),
        "sentence_pairs": sentence_pairs,
        "glossary_matches": glossary_matches,
        "glossary_preservation_rate": round(glossary_preservation_rate, 4),
        "ner_entities": translated_entities,
        "ner_preservation_rate": round(ner_preservation_rate, 4),
        "confidence_score": confidence_result["score"],
        "confidence_level": confidence_result["level"],
        "confidence_breakdown": confidence_result["breakdown"],
        "processing_time_seconds": processing_time,
        "reconstructed_doc": reconstructed_doc,
    }

