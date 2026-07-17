"""
ASR Engine — faster-whisper for audio and video input.
Audio:  MP3/WAV/M4A/OGG/FLAC → transcription
Video:  MP4/AVI/MOV/MKV → extract audio via ffmpeg → transcription
"""

from __future__ import annotations
from pathlib import Path
from typing import List
from utils.logger import app_logger

# Lazy model instance
_whisper_model = None


def _get_whisper():
    """Lazily load faster-whisper small model (~500MB)."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        from config import settings, DEVICE
        app_logger.info(f"Loading faster-whisper '{settings.WHISPER_MODEL_SIZE}' model...")
        compute_type = "float16" if DEVICE == "cuda" else "int8"
        _whisper_model = WhisperModel(
            settings.WHISPER_MODEL_SIZE,
            device=DEVICE,
            compute_type=compute_type,
        )
        app_logger.info("faster-whisper ready.")
    return _whisper_model


def _extract_audio_from_video(video_path: Path) -> Path:
    """Extract audio track from video file using ffmpeg. Returns WAV path."""
    import ffmpeg
    import tempfile

    out_path = Path(tempfile.mktemp(suffix=".wav"))
    app_logger.info(f"Extracting audio from video: {video_path.name}")
    (
        ffmpeg
        .input(str(video_path))
        .output(str(out_path), acodec="pcm_s16le", ar="16000", ac=1)
        .overwrite_output()
        .run(quiet=True)
    )
    app_logger.info(f"Audio extracted to: {out_path}")
    return out_path


def transcribe_audio(audio_path: Path) -> dict:
    """
    Transcribe an audio file using faster-whisper.

    Returns:
        {
            "text": str,                  # full transcript
            "language": str,              # detected ISO code (ne/si/en/etc.)
            "language_probability": float,
            "segments": list[dict]        # per-segment with timestamps
        }
    """
    model = _get_whisper()
    app_logger.info(f"Transcribing audio: {audio_path.name}")

    segments, info = model.transcribe(
        str(audio_path),
        beam_size=5,
        vad_filter=True,           # Remove silence
        vad_parameters={"min_silence_duration_ms": 500},
    )

    segment_list = []
    full_text_parts = []
    for seg in segments:
        segment_list.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })
        full_text_parts.append(seg.text.strip())

    full_text = " ".join(full_text_parts)
    detected_lang = info.language          # e.g. "ne", "si", "en"
    lang_prob = info.language_probability

    app_logger.info(
        f"Transcription complete: lang={detected_lang} ({lang_prob:.2f}), "
        f"{len(full_text)} chars, {len(segment_list)} segments"
    )

    return {
        "text": full_text,
        "language": detected_lang,
        "language_probability": lang_prob,
        "segments": segment_list,
    }


def process_audio(file_path: Path, file_type: str) -> dict:
    """
    Entry point for audio and video files.
    - audio: transcribe directly
    - video: extract audio first, then transcribe
    """
    audio_path = file_path
    tmp_audio = None

    if file_type == "video":
        tmp_audio = _extract_audio_from_video(file_path)
        audio_path = tmp_audio

    try:
        result = transcribe_audio(audio_path)
    finally:
        if tmp_audio and tmp_audio.exists():
            tmp_audio.unlink()

    return result
