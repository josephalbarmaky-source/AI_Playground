"""Voice message transcription via Whisper HTTP service."""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import httpx

from ..config import CONFIG

log = logging.getLogger("dabbar.transcribe")


async def transcribe_voice(file_bytes: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(tmp_path, "rb") as f:
                resp = await client.post(
                    f"{CONFIG.whisper_url}/asr",
                    files={"audio_file": ("voice.ogg", f, "audio/ogg")},
                    params={"task": "transcribe", "language": "auto", "output": "json"},
                )
            resp.raise_for_status()
            result = resp.json()
            return result.get("text", "").strip()
    except Exception as e:
        log.warning("Whisper transcription failed: %s", e)
        return ""
    finally:
        Path(tmp_path).unlink(missing_ok=True)
