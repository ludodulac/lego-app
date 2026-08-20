"""Gemini generateContent provider using the shared BrickHouse vision contract."""
from __future__ import annotations

import base64
import json
import os
from typing import Any

import httpx
from pydantic import ValidationError

from .models import PhotoAnalysisResult
from .openai_provider import PhotoInput, SYSTEM_PROMPT

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
    return text.strip()


def _clean_json_text(text: str) -> str:
    """Accept JSON itself and the common accidental Markdown fence wrapper."""
    value = text.strip()
    if value.startswith("```"):
        lines = value.splitlines()
        if lines and lines[0].strip().lower() in {"```", "```json"}:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        value = "\n".join(lines).strip()
    return value


def _validate_result(text: str) -> PhotoAnalysisResult:
    return PhotoAnalysisResult.model_validate_json(_clean_json_text(text))


def _repair_prompt(invalid_text: str, exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        errors = exc.errors(include_url=False, include_context=False)
    else:
        errors = [{"error": str(exc)}]
    # Do not ask the model to reinterpret the architecture: this pass only
    # repairs JSON/schema/cross-field consistency.
    return (
        "Repair the following BrickHouse photo-analysis candidate so it validates exactly against the supplied JSON schema. "
        "Preserve all architectural observations, dimensions and uncertainty unless a value itself violates a schema or cross-field constraint. "
        "Do not invent missing observations merely to make validation pass. Return JSON only.\n\n"
        f"VALIDATION ERRORS:\n{json.dumps(errors, ensure_ascii=False)}\n\n"
        f"CANDIDATE:\n{invalid_text}"
    )


def _post_json(http: httpx.Client, url: str, key: str, body: dict[str, Any]) -> str:
    response = http.post(
        url,
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json=body,
    )
    response.raise_for_status()
    return _extract_text(response.json())


def analyze_building_photos_gemini(
    photos: list[PhotoInput],
    *,
    user_notes: str = "",
    known_front_width_m: float | None = None,
    client: httpx.Client | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> PhotoAnalysisResult:
    """Analyze 1–6 photos with Gemini and validate/repair the shared result contract."""
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
        raise ValueError("Pour le fournisseur Gemini, réduisez la taille totale des photos sous 14 Mo pour cet essai.")

    selected_model = model or os.getenv("GEMINI_VISION_MODEL", "gemini-3.6-flash")
    key = api_key or os.getenv("GEMINI_API_KEY", "")
    if not key.strip():
        raise ValueError("Gemini API key is not configured")

    parts: list[dict[str, Any]] = [
        {"inline_data": {"mime_type": photo.media_type, "data": base64.b64encode(photo.content).decode("ascii")}}
        for photo in photos
    ]
    parts.append({"text": _prompt(user_notes, known_front_width_m)})
    schema = PhotoAnalysisResult.model_json_schema()
    generation = {"responseMimeType": "application/json", "responseJsonSchema": schema}
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": generation,
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent"
    owns_client = client is None
    http = client or httpx.Client(timeout=90.0)
    try:
        text = _post_json(http, url, key, body)
        try:
            return _validate_result(text)
        except (json.JSONDecodeError, ValidationError, ValueError) as first_error:
            repair_body = {
                "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"role": "user", "parts": [{"text": _repair_prompt(text, first_error)}]}],
                "generationConfig": generation,
            }
            repaired = _post_json(http, url, key, repair_body)
            try:
                return _validate_result(repaired)
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                raise ValueError("vision provider returned invalid structured output after repair") from exc
    finally:
        if owns_client:
            http.close()
