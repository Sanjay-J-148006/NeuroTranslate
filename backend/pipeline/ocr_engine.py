"""
OCR Engine — PaddleOCR wrapper.
Handles image files and scanned PDF pages.
Returns extracted text blocks with bounding boxes.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, TYPE_CHECKING
from utils.logger import app_logger

if TYPE_CHECKING:
    from pipeline.document_parser import TextBlock, ParsedDocument

# Lazy global instance
_ocr_instance = None


def _get_ocr():
    """Lazily initialise PaddleOCR (downloads models on first call)."""
    global _ocr_instance
    if _ocr_instance is None:
        app_logger.info("Initialising PaddleOCR...")
        from paddleocr import PaddleOCR
        # use_angle_cls=True handles rotated text; lang='en' works for multilingual scripts
        # because Nepali/Sinhala detection is done at the text level via FastText after extraction
        import logging
        logging.getLogger('ppocr').setLevel(logging.WARNING)
        _ocr_instance = PaddleOCR(
            use_angle_cls=True,
            lang="en",
        )
        app_logger.info("PaddleOCR ready.")
    return _ocr_instance


def ocr_image(image_path: Path) -> List[dict]:
    """
    Run OCR on a single image file.

    Returns list of:
        {"text": str, "bbox": (x0,y0,x1,y1), "confidence": float}
    """
    from config import DEVICE
    ocr = _get_ocr()

    result = ocr.ocr(str(image_path), cls=True)
    blocks = []

    if not result or result[0] is None:
        app_logger.warning(f"OCR returned no text for {image_path.name}")
        return blocks

    for line in result[0]:
        bbox_points, (text, confidence) = line
        # Convert quad bbox to (x0, y0, x1, y1)
        xs = [p[0] for p in bbox_points]
        ys = [p[1] for p in bbox_points]
        bbox = (min(xs), min(ys), max(xs), max(ys))
        if text.strip():
            blocks.append({"text": text.strip(), "bbox": bbox, "confidence": confidence})

    app_logger.info(f"OCR extracted {len(blocks)} text blocks from {image_path.name}")
    return blocks


def ocr_pdf_pages(pdf_path: Path) -> List[dict]:
    """
    Run OCR on each page of a scanned PDF by rendering pages to images first.
    Uses PyMuPDF to render pages then PaddleOCR to read them.
    """
    import fitz
    import tempfile
    import os

    blocks = []
    pdf = fitz.open(str(pdf_path))

    with tempfile.TemporaryDirectory() as tmp_dir:
        for page_num, page in enumerate(pdf):
            # Render page to image at 200 DPI
            mat = fitz.Matrix(200 / 72, 200 / 72)
            pix = page.get_pixmap(matrix=mat)
            img_path = Path(tmp_dir) / f"page_{page_num:04d}.png"
            pix.save(str(img_path))

            page_blocks = ocr_image(img_path)
            for b in page_blocks:
                b["page_number"] = page_num
            blocks.extend(page_blocks)

    pdf.close()
    app_logger.info(f"OCR processed {len(pdf)} pages, extracted {len(blocks)} total blocks")
    return blocks


def apply_ocr_to_document(doc: "ParsedDocument") -> "ParsedDocument":
    """
    Fill a ParsedDocument's blocks via OCR (for images and scanned PDFs).
    Modifies doc in-place and returns it.
    """
    from pipeline.document_parser import TextBlock

    file_type = doc.file_type
    src = doc.source_path

    if file_type == "image":
        raw_blocks = ocr_image(src)
    elif file_type == "pdf":
        raw_blocks = ocr_pdf_pages(src)
    else:
        app_logger.warning(f"OCR called on unexpected file_type='{file_type}' — skipping")
        return doc

    for i, b in enumerate(raw_blocks):
        doc.blocks.append(TextBlock(
            text=b["text"],
            block_index=i,
            page_number=b.get("page_number", 0),
            block_type="paragraph",
            bbox=b.get("bbox"),
        ))

    doc.needs_ocr = False
    return doc
