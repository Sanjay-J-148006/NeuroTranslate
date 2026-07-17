# NeuroTranslate 🧠

> AI-powered multilingual document translation — Nepali & Sinhala → English  
> Makeathon Edition | FastAPI + React + Vite

---

## Architecture

```
Upload (PDF/Image/DOCX/TXT/Audio/Video)
    ↓ Document Parser / OCR / ASR
    ↓ FastText Language Detection
    ↓ IndicTrans2 (Nepali) | NLLB-200 (Sinhala) | Pass-Through (English)
    ↓ Glossary Engine
    ↓ XLM-RoBERTa NER
    ↓ Confidence Scorer
    ↓ Export PDF / DOCX / TXT
    ↓ Trust Dashboard
```

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- SQLite (built into Python, no server needed!)
- ffmpeg (for audio/video support): https://ffmpeg.org/download.html

### 1. Clone & setup environment
```bash
cp .env.example .env
# SQLite is pre-configured in .env, no edits required!
```

### 2. Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API docs: http://localhost:8000/docs

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

---

## Models (auto-downloaded on first use)

| Model | Size | Purpose |
|---|---|---|
| `ai4bharat/indictrans2-indic-en-dist-200M` | ~500 MB | Nepali → English |
| `facebook/nllb-200-distilled-600M` | ~1.2 GB | Sinhala → English |
| `Davlan/xlm-roberta-base-ner-hrl` | ~1.1 GB | Named Entity Recognition |
| `faster-whisper small` | ~500 MB | Audio/Video transcription |
| FastText `lid.176.bin` | ~130 MB | Language Detection |
| PaddleOCR | ~300 MB | OCR for images/scanned PDFs |

> **Total disk**: ~3.7 GB (downloaded on first run, cached in `~/.cache/huggingface/`)

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `POST /api/translate` | POST | Upload file, start pipeline |
| `GET /api/jobs/{job_id}` | GET | Poll job status + results |
| `GET /api/download/{job_id}/{fmt}` | GET | Download `pdf` / `docx` / `txt` |
| `GET /health` | GET | Health check |
| `GET /docs` | GET | Swagger UI |

---

## Supported Input Formats

| Format | Extensions |
|---|---|
| PDF | `.pdf` |
| Image | `.png .jpg .jpeg .tiff .bmp .webp` |
| DOCX | `.docx` |
| Text | `.txt .csv` |
| Audio | `.mp3 .wav .m4a .ogg .flac` |
| Video (optional) | `.mp4 .avi .mov .mkv` |

---

## RAM Requirements (8 GB Laptop)

- Peak usage: ~6.2 GB (Sinhala path)  
- Models are loaded **lazily** — only one translation model in RAM at a time  
- Works on CPU; GPU auto-detected if available

---

## Confidence Score

| Score | Level |
|---|---|
| 90–100% | ✅ High Confidence |
| 70–89% | ⚠️ Moderate Confidence |
| Below 70% | 🔴 Needs Human Review |

Computed from: Translation Quality (50%) + NER Preservation (20%) + Glossary (15%) + Language Detection (15%)
