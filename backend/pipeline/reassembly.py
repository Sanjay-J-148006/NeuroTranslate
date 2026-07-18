"""
Translation Fusion & Reassembly Module — Clean architecture reassembly engine.
Reconstructs original reading order, tables, lists, and layout structure post-translation.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from utils.logger import app_logger

# ── Translation Chunk ──────────────────────────────────────────────────────────

@dataclass
class TranslationChunk:
    id: int                # Unique ID representing original reading order
    page: int              # Page number (0-indexed)
    paragraph: int         # Paragraph/Block index within page
    sentence: int          # Sentence index within paragraph (1-indexed)
    block_type: str        # heading / paragraph / table_cell / list_item / caption
    text: str              # Source sentence text
    translation: str = ""  # Translated sentence text (English)
    metadata: Dict[str, Any] = field(default_factory=dict) # Structural metadata (e.g. table coordinates)


# ── Reconstructed Structure ────────────────────────────────────────────────────

@dataclass
class ReconstructedParagraph:
    paragraph_index: int
    block_type: str
    source_text: str
    translated_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReconstructedPage:
    page_number: int
    paragraphs: List[ReconstructedParagraph] = field(default_factory=list)


@dataclass
class ReconstructedDocument:
    pages: List[ReconstructedPage] = field(default_factory=list)
    all_paragraphs: List[ReconstructedParagraph] = field(default_factory=list)


# ── Sentence Splitting Utility ──────────────────────────────────────────────────

def _split_into_sentences(text: str) -> List[str]:
    """Split text block into individual sentences based on punctuation."""
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


# ── Pipeline Stages ────────────────────────────────────────────────────────────

def assign_metadata(parsed_doc: Any) -> List[TranslationChunk]:
    """
    Split ParsedDocument TextBlocks into sentence chunks with metadata.
    
    Args:
        parsed_doc: ParsedDocument model from document_parser.py
        
    Returns:
        List of TranslationChunk objects.
    """
    chunks: List[TranslationChunk] = []
    chunk_id = 1

    for block in parsed_doc.blocks:
        sentences = _split_into_sentences(block.text)
        if not sentences:
            continue
            
        for sent_idx, sent in enumerate(sentences, 1):
            chunks.append(TranslationChunk(
                id=chunk_id,
                page=block.page_number,
                paragraph=block.block_index,
                sentence=sent_idx,
                block_type=block.block_type,
                text=sent,
                metadata=block.metadata.copy() if block.metadata else {}
            ))
            chunk_id += 1

    app_logger.info(f"Reassembly: Assigned metadata to {len(chunks)} sentence chunks")
    return chunks


def merge_translation_with_metadata(
    chunks: List[TranslationChunk], 
    translated_data: List[Dict[str, Any]]
) -> List[TranslationChunk]:
    """
    Fuse translated text chunks back with original metadata using unique IDs.
    Handles duplicate or missing chunk IDs with graceful logging error tolerance.
    """
    chunk_map = {c.id: c for c in chunks}
    processed_ids = set()

    for item in translated_data:
        cid = item.get("id")
        trans_text = item.get("translation", "").strip()

        if cid is None:
            app_logger.warning("Reassembly Fusion: Skipped item with missing 'id' key.")
            continue

        if cid in processed_ids:
            app_logger.error(f"Reassembly Fusion: Duplicate chunk ID detected: {cid}")
            continue

        if cid in chunk_map:
            chunk_map[cid].translation = trans_text
            processed_ids.add(cid)
        else:
            app_logger.error(f"Reassembly Fusion: Chunk ID {cid} has no matching metadata block!")

    # Check for missing translation coverage
    untranslated_ids = set(chunk_map.keys()) - processed_ids
    if untranslated_ids:
        app_logger.warning(f"Reassembly Fusion: {len(untranslated_ids)} chunks did not receive translation.")
        # Fill missing with original source text to prevent empty gaps
        for uid in untranslated_ids:
            chunk_map[uid].translation = chunk_map[uid].text

    return chunks


def sort_chunks(chunks: List[TranslationChunk]) -> List[TranslationChunk]:
    """Sort chunks by page number, paragraph index, then sentence index."""
    return sorted(chunks, key=lambda x: (x.page, x.paragraph, x.sentence))


def reconstruct_document(chunks: List[TranslationChunk]) -> ReconstructedDocument:
    """
    Reassemble translated chunks into pages, paragraphs, lists, and tables.
    """
    sorted_chunks = sort_chunks(chunks)
    reconstructed_doc = ReconstructedDocument()

    # Step 1: Group chunks by (page, paragraph) to reconstruct paragraphs
    paragraph_groups: Dict[Tuple[int, int], List[TranslationChunk]] = {}
    for c in sorted_chunks:
        key = (c.page, c.paragraph)
        if key not in paragraph_groups:
            paragraph_groups[key] = []
        paragraph_groups[key].append(c)

    # Step 2: Build reconstructed paragraphs
    page_paragraphs_map: Dict[int, List[ReconstructedParagraph]] = {}

    for (page_num, para_num), p_chunks in paragraph_groups.items():
        first_chunk = p_chunks[0]
        
        # Merge sentences back together
        src_text = " ".join(c.text for c in p_chunks)
        trans_text = " ".join(c.translation for c in p_chunks)

        reconstructed_para = ReconstructedParagraph(
            paragraph_index=para_num,
            block_type=first_chunk.block_type,
            source_text=src_text,
            translated_text=trans_text,
            metadata=first_chunk.metadata.copy()
        )

        if page_num not in page_paragraphs_map:
            page_paragraphs_map[page_num] = []
        page_paragraphs_map[page_num].append(reconstructed_para)

    # Step 3: Build pages and document structure
    for page_num in sorted(page_paragraphs_map.keys()):
        paras = sorted(page_paragraphs_map[page_num], key=lambda x: x.paragraph_index)
        page = ReconstructedPage(page_number=page_num, paragraphs=paras)
        
        reconstructed_doc.pages.append(page)
        reconstructed_doc.all_paragraphs.extend(paras)

    app_logger.info(
        f"Reassembly COMPLETE: Document contains {len(reconstructed_doc.pages)} pages, "
        f"{len(reconstructed_doc.all_paragraphs)} paragraphs/layout structures."
    )
    return reconstructed_doc
