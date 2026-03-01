"""
AURA – Audio Utilities

text_to_speech(text) → bytes (MP3)   using gTTS
Streamlit audio input is handled natively via st.audio_input() in the page.
"""
from __future__ import annotations
import io
import logging

logger = logging.getLogger(__name__)


def text_to_speech(text: str, lang: str = "en") -> bytes | None:
    """
    Convert text to speech MP3 bytes using gTTS.
    Returns None if gTTS is not installed or conversion fails.
    """
    try:
        from gtts import gTTS  # type: ignore
        # Truncate very long responses for audio readability
        tts_text = text[:2000] if len(text) > 2000 else text
        # Strip markdown for cleaner speech
        import re
        tts_text = re.sub(r"\*\*|__|\*|`|#{1,6}\s?|>\s?|\[!\]", "", tts_text)
        tts_text = re.sub(r"\|[^\n]+\|", "", tts_text)  # strip tables
        tts_text = re.sub(r"\n{2,}", ". ", tts_text).strip()

        buf = io.BytesIO()
        gTTS(text=tts_text, lang=lang, slow=False).write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except ImportError:
        logger.warning("gTTS not installed — audio output unavailable.")
        return None
    except Exception as exc:
        logger.warning("TTS failed: %s", exc)
        return None
