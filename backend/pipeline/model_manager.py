"""
Model Lifecycle Manager for NeuroTranslate.
Orchestrates lazy-loading, dynamic CPU quantization (INT8), thread optimization,
and explicit memory unloading/garbage collection for:
- NLLB-200 (CTranslate2)
- IndicTrans2 (PyTorch Seq2Seq)
- XLM-RoBERTa NER (Transformers Pipeline)
"""

import gc
import psutil
import torch
from typing import Optional
from utils.logger import app_logger
from config import settings, DEVICE

# ── Global Model States ───────────────────────────────────────────────────────
_nllb_translator = None
_nllb_tokenizer = None

_indictrans_model = None
_indictrans_tokenizer = None

_ner_pipeline = None

# Cache thread configuration
_threads_configured = False


def _configure_threads():
    """Limit PyTorch and standard library threads to physical cores to prevent thrashing."""
    global _threads_configured
    if _threads_configured:
        return

    physical_cores = psutil.cpu_count(logical=False) or 4
    torch.set_num_threads(physical_cores)
    app_logger.info(f"Set PyTorch threads to {physical_cores} physical CPU cores.")
    _threads_configured = True


def _run_gc():
    """Run garbage collection and clear GPU cache if available."""
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# ── NLLB-200 (CTranslate2) ────────────────────────────────────────────────────

def get_nllb():
    """Get or load the CTranslate2 NLLB-200 model."""
    global _nllb_translator, _nllb_tokenizer
    _configure_threads()

    if _nllb_translator is not None:
        return _nllb_translator, _nllb_tokenizer

    # Unload IndicTrans2 if loaded to make room in RAM
    unload_indictrans2()

    app_logger.info("Loading NLLB-200 CTranslate2 model...")
    import ctranslate2
    import transformers
    from huggingface_hub import snapshot_download

    # Helper function to try loading locally first
    def load_snapshot(local_only: bool):
        return snapshot_download(settings.NLLB_MODEL, local_files_only=local_only)

    try:
        model_dir = load_snapshot(local_only=True)
    except Exception:
        app_logger.info(f"Local files for {settings.NLLB_MODEL} not found. Downloading...")
        model_dir = load_snapshot(local_only=False)

    try:
        _nllb_tokenizer = transformers.AutoTokenizer.from_pretrained(
            "facebook/nllb-200-distilled-600M",
            local_files_only=True
        )
    except Exception:
        _nllb_tokenizer = transformers.AutoTokenizer.from_pretrained(
            "facebook/nllb-200-distilled-600M",
            local_files_only=False
        )

    physical_cores = psutil.cpu_count(logical=False) or 4
    _nllb_translator = ctranslate2.Translator(
        model_dir,
        device=DEVICE,
        compute_type="int8" if DEVICE == "cpu" else "float16",
        intra_threads=physical_cores
    )

    app_logger.info("NLLB-200 CTranslate2 model loaded successfully.")
    return _nllb_translator, _nllb_tokenizer


def unload_nllb():
    """Unload NLLB-200 model from RAM."""
    global _nllb_translator, _nllb_tokenizer
    if _nllb_translator is not None:
        _nllb_translator = None
        _nllb_tokenizer = None
        _run_gc()
        app_logger.info("NLLB-200 translation model unloaded.")


# ── IndicTrans2 (PyTorch Seq2Seq) ─────────────────────────────────────────────

def get_indictrans2():
    """Get or load the IndicTrans2 model with Dynamic Quantization on CPU."""
    global _indictrans_model, _indictrans_tokenizer
    _configure_threads()

    if _indictrans_model is not None:
        return _indictrans_model, _indictrans_tokenizer

    # Unload NLLB-200 if loaded to make room in RAM
    unload_nllb()

    app_logger.info("Loading IndicTrans2 model...")
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    model_name = settings.INDICTRANS2_MODEL
    hf_token = settings.HF_TOKEN if settings.HF_TOKEN else None
    if hf_token:
        app_logger.info("Using HF_TOKEN from .env for authenticated download.")
    else:
        app_logger.warning("No HF_TOKEN found — IndicTrans2 may fail (gated repo). Add token to .env.")

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True, local_files_only=True, token=hf_token
        )
    except Exception:
        app_logger.info(f"Local files for {model_name} tokenizer not found. Downloading with HF token...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True, local_files_only=False, token=hf_token
        )

    try:
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            local_files_only=True,
            torch_dtype=torch.float32,
            token=hf_token
        )
    except Exception:
        app_logger.info(f"Local files for {model_name} model not found. Downloading with HF token...")
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            local_files_only=False,
            torch_dtype=torch.float32,
            token=hf_token
        )

    # Dynamic INT8 quantization for CPU (shrinks model from 500MB to ~130MB in RAM, 3x faster)
    if DEVICE == "cpu":
        app_logger.info("Applying dynamic INT8 quantization to IndicTrans2 model...")
        import torch.quantization
        model = torch.quantization.quantize_dynamic(
            model, {torch.nn.Linear}, dtype=torch.qint8
        )

    _indictrans_model = model.to(DEVICE)
    _indictrans_tokenizer = tokenizer

    app_logger.info("IndicTrans2 model loaded and ready.")
    return _indictrans_model, _indictrans_tokenizer


def unload_indictrans2():
    """Unload IndicTrans2 model from RAM."""
    global _indictrans_model, _indictrans_tokenizer
    if _indictrans_model is not None:
        _indictrans_model = None
        _indictrans_tokenizer = None
        _run_gc()
        app_logger.info("IndicTrans2 translation model unloaded.")


# ── XLM-RoBERTa NER (Transformers Pipeline) ───────────────────────────────────

def get_ner():
    """Get or load the XLM-RoBERTa NER model with dynamic dynamic quantization on CPU."""
    global _ner_pipeline
    _configure_threads()

    if _ner_pipeline is not None:
        return _ner_pipeline

    app_logger.info("Loading XLM-RoBERTa NER model...")
    from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline

    model_name = settings.NER_MODEL

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=True)
    except Exception:
        app_logger.info(f"Local files for {model_name} tokenizer not found. Downloading...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, local_files_only=False)

    try:
        model = AutoModelForTokenClassification.from_pretrained(model_name, local_files_only=True)
    except Exception:
        app_logger.info(f"Local files for {model_name} model not found. Downloading...")
        model = AutoModelForTokenClassification.from_pretrained(model_name, local_files_only=False)

    # Dynamic dynamic INT8 quantization for CPU (shrinks model from 1.1GB to ~270MB in RAM, 3x-4x faster)
    if DEVICE == "cpu":
        app_logger.info("Applying dynamic INT8 quantization to NER model...")
        import torch.quantization
        model = torch.quantization.quantize_dynamic(
            model, {torch.nn.Linear}, dtype=torch.qint8
        )

    _ner_pipeline = pipeline(
        "token-classification",
        model=model,
        tokenizer=tokenizer,
        aggregation_strategy="simple",
        device=0 if DEVICE == "cuda" else -1,
    )

    app_logger.info("NER pipeline loaded successfully.")
    return _ner_pipeline


def unload_ner():
    """Unload NER pipeline from RAM."""
    global _ner_pipeline
    if _ner_pipeline is not None:
        _ner_pipeline = None
        _run_gc()
        app_logger.info("NER model unloaded.")


# ── Global Unloading ──────────────────────────────────────────────────────────

def unload_all():
    """Unload all models from memory."""
    unload_nllb()
    unload_indictrans2()
    unload_ner()
