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

Architectural interpretation rules:
- Describe the real building as faithfully as the current BuildingModel schema allows; do NOT force every property into the LEGO engine's current M0 limitations.
- Use multiple rectangular volumes when a materially visible extension/garage/wing cannot honestly be represented by one rectangle.
- Represent a roof as gable only when the photos support a two-slope gable roof. Represent a clearly flat roof as flat.
- If the roof is materially different from both supported schema types, do not silently relabel it as gable. Omit an unsupported/uncertain roof if necessary, set needs_confirmation=true, explain the limitation in assumptions, and ask a required clarification question.
- Detect/estimate facade doors and windows that materially affect the miniature.
- If a side or the rear is missing, prefer the simplest coherent continuation supported by visible evidence; do not invent elaborate hidden extensions.

Perspective and proportion rules — critical:
- Never treat raw image pixel distances as real-world distances when the facade is oblique to the camera.
- Explicitly reason about perspective: parallel architectural lines may converge in the image, nearer openings may appear larger, and vertical dimensions photographed from ground level are foreshortened.
- Recover proportions from repeated architectural alignments and ratios on the same physical plane: wall edge -> opening, opening width, gap between openings, opening -> opposite wall edge, ground -> sill, window -> eaves, eaves -> ridge.
- Prefer ratios measured along the same facade plane, then reconcile those ratios across other views of that facade/building.
- Use corners, eaves, ridge lines, floor bands, window rows and repeated openings as geometric constraints. Symmetry may be evidence but must not be assumed when the photos contradict it.
- Cross-check every important dimension against all useful photos. When two views disagree because of perspective or occlusion, prefer the interpretation that is geometrically consistent across views and lower confidence rather than averaging blindly.
- If a facade is photographed close to straight-on, use it as the strongest source for horizontal opening placement on that facade. Oblique views are especially useful for depth and corner relationships.
- If known_front_width_m is supplied, it is the primary metric scale anchor. First recover normalized facade proportions, then convert those ratios to meters using that known width. Do not independently rescale each opening.
- If no real dimension is known, preserve normalized proportions consistently and choose only a provisional metric scale. State exactly what was used as the provisional scale basis and request one useful measurement.
- For every important inferred proportion, populate proportion_evidence with the facade, observation, method and confidence. scale_basis must explain how metric scale was established.
- If perspective, cropping, vegetation, parked cars or another obstruction makes an important spacing unreliable, mark the evidence as uncertain and ask a clarification question when the uncertainty could materially change the miniature.

Evidence and uncertainty rules:
- SourceInfo is essential: use observed for details clearly visible in photos, user_provided for facts in user notes/known measurements, inferred for geometric completion, generated_default only for deliberate fallback values.
- Confidence must reflect uncertainty. Set needs_confirmation=true whenever an impactful dimension, hidden facade, roof geometry, extension, terrace, opening layout, or scale is uncertain.
- Ask concise clarification questions only for uncertainties that could materially change the miniature.
- Do not claim unseen details are observed.
- Keep every opening inside its facade and avoid overlapping openings.
- Use unique IDs. Units must be meters.
- metadata.created_from must be photo_analysis.

Important separation of responsibilities:
The downstream BrickHouse compatibility layer decides whether the current LEGO engine can build the proposal. Your job is to understand the photographed architecture honestly, not to make an unsupported house look artificially compatible.
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
        "Recover normalized architectural proportions before assigning metric dimensions. "
        "Correct mentally for perspective and cross-check wall-edge/opening/roof spacing across all available views. "
        "Return the most faithful conservative proposal allowed by the BuildingModel schema, plus questions, assumptions, scale_basis and proportion_evidence. "
        "Never change an observed architectural feature merely to make the proposal compatible with the current LEGO engine."
    )
    content: list[dict[str, object]] = [{"type": "input_text", "text": prompt}]
    content.extend({"type": "input_image", "image_url": _data_url(photo), "detail": "high"} for photo in photos)

    api = client or OpenAI()
    response = api.responses.create(
        model=model or os.getenv("OPENAI_VISION_MODEL", "gpt-5"),
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
