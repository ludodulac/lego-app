"""OpenAI Responses API provider for conservative building reconstruction from photos."""
from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass

from openai import OpenAI

from .models import PhotoAnalysisResult


@dataclass(frozen=True)
class PhotoInput:
    content: bytes
    media_type: str
    filename: str


SYSTEM_PROMPT = """You are the architectural interpretation layer of BrickHouse.
Your output is NOT a brick model. Produce a conservative BuildingModel v0.1 proposal from the supplied property photos and user notes.

M0 capabilities and rules:
- Model one main detached-house volume as a rectangular prism.
- Model a gable roof only.
- Detect/estimate facade doors and windows that materially affect the miniature.
- If a side or the rear is missing, prefer the simplest coherent rectangular continuation; do not invent elaborate hidden extensions.
- If absolute scale is unknown, create a plausible provisional metric scale and explicitly list the assumption and ask for a useful real measurement. If known_front_width_m is supplied, use it as the primary scale anchor.
- SourceInfo is essential: use observed for details clearly visible in photos, user_provided for facts in user notes/known measurements, inferred for geometric completion, generated_default only for deliberate fallback values.
- Confidence must reflect uncertainty. Set needs_confirmation=true whenever an impactful dimension, hidden facade, roof geometry, extension, terrace, opening layout, or scale is uncertain.
- Ask concise clarification questions for uncertainties that could materially change the brick model.
- Do not claim unseen details are observed.
- Keep every opening inside its facade and avoid overlapping openings.
- Use unique IDs. Units must be meters.
- metadata.created_from must be photo_analysis.
"""


def _data_url(photo: PhotoInput) -> str:
    encoded = base64.b64encode(photo.content).decode("ascii")
    return f"data:{photo.media_type};base64,{encoded}"


def analyze_building_photos(
    photos: list[PhotoInput],
    *,
    user_notes: str = "",
    known_front_width_m: float | None = None,
    client: OpenAI | None = None,
    model: str | None = None,
) -> PhotoAnalysisResult:
    """Analyze 1–6 photos and return a validated architectural proposal."""
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

    prompt = (
        "Analyze these photos as different views of the same property. "
        f"User notes: {user_notes.strip() or 'none provided'}. "
        f"Known front width in meters: {known_front_width_m if known_front_width_m is not None else 'unknown'}. "
        "Return the best conservative complete proposal plus questions and assumptions."
    )
    content: list[dict[str, object]] = [{"type": "input_text", "text": prompt}]
    content.extend({"type": "input_image", "image_url": _data_url(photo), "detail": "high"} for photo in photos)

    api = client or OpenAI()
    response = api.responses.create(
        model=model or os.getenv("OPENAI_VISION_MODEL", "gpt-5.6-terra"),
        instructions=SYSTEM_PROMPT,
        input=[{"role": "user", "content": content}],
        text={
            "format": {
                "type": "json_schema",
                "name": "brickhouse_photo_analysis",
                "schema": PhotoAnalysisResult.model_json_schema(),
                "strict": False,
            }
        },
    )
    if not response.output_text:
        raise ValueError("vision provider returned no structured output")
    try:
        payload = json.loads(response.output_text)
    except json.JSONDecodeError as exc:
        raise ValueError("vision provider returned invalid JSON") from exc
    return PhotoAnalysisResult.model_validate(payload)
