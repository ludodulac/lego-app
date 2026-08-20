"""Explicit provider selection for BrickHouse photo analysis.

Provider choice is configuration, not inference: this prevents a secret appearing on
an environment from silently changing where house photos are sent.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

from .gemini_provider import analyze_building_photos_gemini
from .models import PhotoAnalysisResult
from .openai_provider import PhotoInput, analyze_building_photos

VisionProviderName = Literal["openai", "gemini"]


class VisionProviderError(RuntimeError):
    """Safe provider-facing failure suitable for conversion to HTTP 502."""


@dataclass(frozen=True)
class VisionStatus:
    ready: bool
    provider: VisionProviderName | None
    model: str | None
    reason: str


def configured_provider() -> str:
    return os.getenv("BRICKHOUSE_VISION_PROVIDER", "none").strip().lower() or "none"


def vision_status() -> VisionStatus:
    provider = configured_provider()
    if provider == "none":
        return VisionStatus(False, None, None, "provider_not_selected")
    if provider == "openai":
        if not os.getenv("OPENAI_API_KEY", "").strip():
            return VisionStatus(False, "openai", None, "missing_server_api_key")
        return VisionStatus(True, "openai", os.getenv("OPENAI_VISION_MODEL", "gpt-5").strip() or "gpt-5", "ready")
    if provider == "gemini":
        if not os.getenv("GEMINI_API_KEY", "").strip():
            return VisionStatus(False, "gemini", None, "missing_server_api_key")
        return VisionStatus(True, "gemini", os.getenv("GEMINI_VISION_MODEL", "gemini-3.6-flash").strip() or "gemini-3.6-flash", "ready")
    return VisionStatus(False, None, None, "unknown_provider")


def analyze_with_configured_provider(
    photos: list[PhotoInput],
    *,
    user_notes: str = "",
    known_front_width_m: float | None = None,
) -> PhotoAnalysisResult:
    status = vision_status()
    if not status.ready or status.provider is None:
        raise VisionProviderError(f"vision provider is not ready: {status.reason}")
    try:
        if status.provider == "openai":
            return analyze_building_photos(
                photos,
                user_notes=user_notes,
                known_front_width_m=known_front_width_m,
                model=status.model,
            )
        return analyze_building_photos_gemini(
            photos,
            user_notes=user_notes,
            known_front_width_m=known_front_width_m,
            model=status.model,
        )
    except ValueError:
        raise
    except Exception as exc:
        # Provider SDK/HTTP exceptions should never leak response bodies, keys or
        # account details through the public BrickHouse API.
        raise VisionProviderError("configured vision provider failed") from exc
