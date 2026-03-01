"""
HALO Health – Dynamic Gemini Model Selector

Calls genai.list_models() at startup and picks the strongest available
models for "pro" (complex reasoning, multimodal) and "flash" (fast, cost-effective)
tiers. Falls back to stable known models if the API call fails.
"""
import logging
from functools import lru_cache
from typing import Tuple

import google.generativeai as genai

logger = logging.getLogger(__name__)

# ── Priority-ordered candidate lists (strongest first) ──────────────────────
# These are checked in order; the first one found in list_models() wins.
# Using FREE TIER models only (gemini-2.5-flash is free)
PRO_CANDIDATES = [
    "gemini-2.5-flash",  # Free tier - use for all
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
]

FLASH_CANDIDATES = [
    "gemini-2.5-flash",  # Free tier
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash",
]


@lru_cache(maxsize=1)
def select_models() -> Tuple[str, str]:
    """
    Dynamically select the best available Pro and Flash Gemini models.

    Returns:
        (pro_model_name, flash_model_name) – short names without 'models/' prefix.
    """
    try:
        available = set()
        for m in genai.list_models():
            # Only consider models that support generateContent
            if "generateContent" in m.supported_generation_methods:
                # Strip the 'models/' prefix for clean comparison
                name = m.name.replace("models/", "")
                available.add(name)

        logger.info("Available Gemini models (%d): %s", len(available), sorted(available))

        pro = _pick(PRO_CANDIDATES, available, fallback="gemini-2.5-flash")
        flash = _pick(FLASH_CANDIDATES, available, fallback="gemini-2.5-flash")

        logger.info("Selected → PRO: %s | FLASH: %s", pro, flash)
        return pro, flash

    except Exception as exc:
        logger.warning(
            "Model selection via list_models() failed (%s). Using fallbacks.", exc
        )
        return "gemini-2.5-flash", "gemini-2.5-flash"


def _pick(candidates: list, available: set, fallback: str) -> str:
    for candidate in candidates:
        if candidate in available:
            return candidate
    # If none of our priority candidates are available, return the fallback
    logger.warning("None of the preferred models found in available set. Using %s", fallback)
    return fallback


def get_pro_model() -> str:
    return select_models()[0]


def get_flash_model() -> str:
    return select_models()[1]
