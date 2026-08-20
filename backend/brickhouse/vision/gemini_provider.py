"""Gemini generateContent provider using the same BrickHouse vision contract."""
from __future__ import annotations

import base64
import json
import os
from typing import Any

import httpx

from .models import PhotoAnalysisResult
from .openai_provider import PhotoInput, SYSTEM_PROMPT

# Google documents a <20MB total inline request limit. Base64 expands bytes by
# roughly 4/3 and the schema/prompt also consume request space, so stay below
# 14 MiB raw image bytes for a conservative M0 inline request.
MAX_GEMINI_INLINE_RAW_BYTES = 14 * 1024 * 1024


def _prompt(user_notes: str, known_front_width_m: float | None) -> str:
    return (
        "Analyze these photos as different views of the same property. "
        f"User notes: {user_notes.strip() or 'none provided'}. "
        f"Known front width in meters: {known_front_width_m if known_front_width_m is not None else 'unknown'}. "
        "Return the most faithful conservative proposal allowed by the BuildingModel schema, plus questions and assumptions. "
        "Never change an observed architectural feature merely to make the proposal compatible with the current LEGO engine."
    )


def _extract_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates") or []
    if not candidates:
        raise ValueError("vision provider returned no candidate")
    parts = ((candidates[0].get("content") or {}).get("parts") or [])
    text = "".join(str(part.get("text", "")) for part in parts if part.get("text"))
    if not text:
        raise ValueError("vision provider returned no structured output")
    return text


def analyze_building_photos_gemini(
    photos: list[PhotoInput],
    *,
    user_notes: str = "",
    known_front_width_m: float | None = None,
    client: httpx.Client | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> PhotoAnalysisResult:
    """Analyze 1–6 photos with Gemini and validate the shared result contract."""
    if not 1 <= len(photos) <= 6:
        raise ValueError("photo analysis requires between 1 and 6 images")
    if known_front_width_m is not None and known_front_width_m <= 0:
        raise ValueError("known_front_width_m must be positive")
    supported = {"image/jpeg", "image/png", "image/webp"}
    for photo in photos:
        if photo.media_type not in supported:
            raise ValueError(f"unsupported image type: {photo.media_type}")
        if not photo.content:
            raise ValueError(f"empty image: {photo.filename}")
    if sum(len(photo.content) for photo in photos) > MAX_GEMINI_INLINE_RAW_BYTES:
        raise ValueError(
            "Pour le fournisseur Gemini, réduisez la taille totale des photos sous 14 Mo pour cet essai."
        )

    selected_model = model or os.getenv("GEMINI_VISION_MODEL", "gemini-3.6-flash")
    key = api_key or os.getenv("GEMINI_API_KEY", "")
    if not key.strip():
        raise ValueError("Gemini API key is not configured")

    parts: list[dict[str, Any]] = []
    for photo in photos:
        parts.append({
            "inline_data": {
                "mime_type": photo.media_type,
                "data": base64.b64encode(photo.content).decode("ascii"),
            }
        })
    parts.append({"text": _prompt(user_notes, known_front_width_m)})
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": PhotoAnalysisResult.model_json_schema(),
        },
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent"
    owns_client = client is None
    http = client or httpx.Client(timeout=90.0)
    try:
        response = http.post(
            url,
            headers={"x-goog-api-key": key, "Content-Type": "application/json"},
            json=body,
        )
        response.raise_for_status()
        text = _extract_text(response.json())
    finally:
        if owns_client:
            http.close()
    try:
        return PhotoAnalysisResult.model_validate_json(text)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("vision provider returned invalid structured output") from exc
