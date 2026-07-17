"""
Export Engine — Generate translated documents in PDF, DOCX, and TXT formats.
Preserves structure: headings, paragraphs, tables.
"""

from __future__ import annotations
import uuid
from pathlib import Path
from typing import List
from config import settings
from utils.logger import app_logger


def _ensure_export_dir() -> Path:
    settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    return settings.EXPORT_DIR


# ── TXT Export ────────────────────────────────────────────────────────────────

def export_txt(
    job_id: str,
    source_text: str,
    translated_text: str,
    detected_language: str,
    confidence_score: float,
) -> Path:
    export_dir = _ensure_export_dir()
    out_path = export_dir / f"{job_id}_translated.txt"

    lang_label = {"ne": "Nepali", "si": "Sinhala", "en": "English"}.get(detected_language, "Unknown")

    content = (
        f"NeuroTranslate — Translation Export\n"
        f"{'='*50}\n"
        f"Source Language: {lang_label}\n"
        f"Confidence Score: {confidence_score:.1f}%\n"
        f"{'='*50}\n\n"
        f"ORIGINAL TEXT:\n{'-'*30}\n{source_text}\n\n"
        f"TRANSLATED TEXT (English):\n{'-'*30}\n{translated_text}\n"
    )

    out_path.write_text(content, encoding="utf-8")
    app_logger.info(f"TXT export: {out_path}")
    return out_path


# ── DOCX Export ───────────────────────────────────────────────────────────────

def export_docx(
    job_id: str,
    source_text: str,
    translated_text: str,
    detected_language: str,
    confidence_score: float,
    entities: List[dict] | None = None,
) -> Path:
    from docx import Document
    from docx.shared import Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    export_dir = _ensure_export_dir()
    out_path = export_dir / f"{job_id}_translated.docx"
    lang_label = {"ne": "Nepali", "si": "Sinhala", "en": "English"}.get(detected_language, "Unknown")

    doc = Document()

    # Title
    title = doc.add_heading("NeuroTranslate — Translation Report", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Metadata table
    meta_table = doc.add_table(rows=3, cols=2)
    meta_table.style = "Table Grid"
    meta_data = [
        ("Source Language", lang_label),
        ("Confidence Score", f"{confidence_score:.1f}%"),
        ("Model", "IndicTrans2" if detected_language == "ne" else "NLLB-200" if detected_language == "si" else "Pass-Through"),
    ]
    for i, (k, v) in enumerate(meta_data):
        meta_table.rows[i].cells[0].text = k
        meta_table.rows[i].cells[1].text = v

    doc.add_paragraph()

    # Original text
    doc.add_heading("Original Text", level=1)
    for para in source_text.split("\n\n"):
        if para.strip():
            doc.add_paragraph(para.strip())

    doc.add_paragraph()

    # Translated text
    doc.add_heading("English Translation", level=1)
    for para in translated_text.split("\n\n"):
        if para.strip():
            doc.add_paragraph(para.strip())

    # NER section
    if entities:
        doc.add_paragraph()
        doc.add_heading("Named Entities Detected", level=1)
        ner_table = doc.add_table(rows=1, cols=3)
        ner_table.style = "Table Grid"
        hdr = ner_table.rows[0].cells
        hdr[0].text = "Entity"
        hdr[1].text = "Type"
        hdr[2].text = "Confidence"
        for ent in entities[:50]:
            row = ner_table.add_row().cells
            row[0].text = ent.get("text", "")
            row[1].text = ent.get("label", "")
            row[2].text = f"{ent.get('score', 0) * 100:.1f}%"

    doc.save(str(out_path))
    app_logger.info(f"DOCX export: {out_path}")
    return out_path


# ── PDF Export ────────────────────────────────────────────────────────────────

def export_pdf(
    job_id: str,
    source_text: str,
    translated_text: str,
    detected_language: str,
    confidence_score: float,
    entities: List[dict] | None = None,
) -> Path:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    export_dir = _ensure_export_dir()
    out_path = export_dir / f"{job_id}_translated.pdf"
    lang_label = {"ne": "Nepali", "si": "Sinhala", "en": "English"}.get(detected_language, "Unknown")

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=18, spaceAfter=16, textColor=colors.HexColor("#1a1a2e"),
    )
    heading_style = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        fontSize=13, spaceAfter=8, textColor=colors.HexColor("#16213e"),
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, spaceAfter=6, leading=14,
    )
    meta_style = ParagraphStyle(
        "Meta", parent=styles["Normal"],
        fontSize=9, textColor=colors.grey,
    )

    story = []

    # Title
    story.append(Paragraph("NeuroTranslate — Translation Report", title_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#6c63ff")))
    story.append(Spacer(1, 0.4*cm))

    # Metadata
    conf_color = "#22c55e" if confidence_score >= 90 else "#f59e0b" if confidence_score >= 70 else "#ef4444"
    model_used = "IndicTrans2" if detected_language == "ne" else "NLLB-200" if detected_language == "si" else "Pass-Through"
    meta_data = [
        ["Source Language", lang_label],
        ["Translation Model", model_used],
        ["Confidence Score", f"{confidence_score:.1f}%"],
    ]
    meta_table = Table(meta_data, colWidths=[5*cm, 12*cm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f4ff")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d7ff")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f9faff")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.5*cm))

    # Original text
    story.append(Paragraph("Original Text", heading_style))
    for para in source_text.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip().replace("\n", "<br/>"), body_style))
    story.append(Spacer(1, 0.5*cm))

    # Translated text
    story.append(Paragraph("English Translation", heading_style))
    for para in translated_text.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip().replace("\n", "<br/>"), body_style))

    # NER section
    if entities:
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("Named Entities Detected", heading_style))
        ner_data = [["Entity", "Type", "Score"]]
        for ent in entities[:30]:
            ner_data.append([ent.get("text",""), ent.get("label",""), f"{ent.get('score',0)*100:.1f}%"])
        ner_table = Table(ner_data, colWidths=[8*cm, 4*cm, 3*cm])
        ner_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6c63ff")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9faff")]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(ner_table)

    doc.build(story)
    app_logger.info(f"PDF export: {out_path}")
    return out_path


# ── Dispatcher ────────────────────────────────────────────────────────────────

def export_all(job_id: str, result: dict) -> dict:
    """Generate PDF, DOCX, and TXT exports. Returns dict of paths."""
    kwargs = dict(
        job_id=job_id,
        source_text=result.get("source_text", ""),
        translated_text=result.get("translated_text", ""),
        detected_language=result.get("detected_language", "en"),
        confidence_score=result.get("confidence_score", 0.0),
        entities=result.get("ner_entities"),
    )

    paths = {}
    try:
        paths["pdf"] = str(export_pdf(**kwargs))
    except Exception as e:
        app_logger.error(f"PDF export failed: {e}")
        paths["pdf"] = None

    try:
        paths["docx"] = str(export_docx(**kwargs))
    except Exception as e:
        app_logger.error(f"DOCX export failed: {e}")
        paths["docx"] = None

    try:
        paths["txt"] = str(export_txt(
            job_id=job_id,
            source_text=result.get("source_text", ""),
            translated_text=result.get("translated_text", ""),
            detected_language=result.get("detected_language", "en"),
            confidence_score=result.get("confidence_score", 0.0),
        ))
    except Exception as e:
        app_logger.error(f"TXT export failed: {e}")
        paths["txt"] = None

    return paths
