"""Bounded local geometric validation for provider-proposed architectural landmarks.

This module never discovers cross-view identity. It only refines or rejects the
location of a landmark whose physical identity was already proposed explicitly by
the vision layer. The search is confined to a small neighbourhood around that
proposal and is repeated under deterministic seed perturbations to measure local
stability.
"""
from __future__ import annotations

from typing import Literal

import cv2
import numpy as np
from pydantic import BaseModel, Field, model_validator

from .photo_rectification import NormalizedImagePoint


LocalLandmarkStatus = Literal["ACCEPTED", "REJECTED"]


class LocalLandmarkValidation(BaseModel):
    physical_landmark_id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    status: LocalLandmarkStatus
    proposed_point: NormalizedImagePoint
    refined_point: NormalizedImagePoint | None = None
    repeatability_rms_px: float | None = Field(default=None, ge=0)
    localization_shift_px: float | None = Field(default=None, ge=0)
    successful_trials: int = Field(ge=0)
    total_trials: int = Field(ge=1)
    diagnostic: str

    @model_validator(mode="after")
    def validate_status(self) -> "LocalLandmarkValidation":
        if self.status == "ACCEPTED":
            if self.refined_point is None or self.repeatability_rms_px is None or self.localization_shift_px is None:
                raise ValueError("accepted local landmark validation requires refined point and stability metrics")
        elif self.refined_point is not None:
            raise ValueError("rejected local landmark validation must not expose a refined point")
        return self


def _decode_gray(content: bytes) -> np.ndarray:
    encoded = np.frombuffer(content, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_GRAYSCALE)
    if image is None or image.ndim != 2:
        raise ValueError("photo bytes could not be decoded for local landmark validation")
    return image


def _refine_one(gray: np.ndarray, seed_x: float, seed_y: float, radius: int) -> tuple[float, float] | None:
    height, width = gray.shape
    x0 = max(0, int(round(seed_x)) - radius)
    y0 = max(0, int(round(seed_y)) - radius)
    x1 = min(width, int(round(seed_x)) + radius + 1)
    y1 = min(height, int(round(seed_y)) + radius + 1)
    patch = gray[y0:y1, x0:x1]
    if patch.shape[0] < 9 or patch.shape[1] < 9:
        return None
    corners = cv2.goodFeaturesToTrack(
        patch,
        maxCorners=4,
        qualityLevel=0.04,
        minDistance=4,
        blockSize=5,
        useHarrisDetector=True,
        k=0.04,
    )
    if corners is None:
        return None
    absolute = []
    for value in corners.reshape(-1, 2):
        absolute.append((float(value[0] + x0), float(value[1] + y0)))
    absolute.sort(key=lambda point: ((point[0] - seed_x) ** 2 + (point[1] - seed_y) ** 2, point[1], point[0]))
    selected = np.array([[absolute[0]]], dtype=np.float32)
    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)
    try:
        cv2.cornerSubPix(gray, selected, (4, 4), (-1, -1), criteria)
    except cv2.error:
        return absolute[0]
    return float(selected[0, 0, 0]), float(selected[0, 0, 1])


def validate_local_landmark(
    content: bytes,
    *,
    physical_landmark_id: str,
    photo_index: int,
    proposed_point: NormalizedImagePoint,
    search_radius_px: int = 24,
    perturbation_px: int = 4,
    maximum_repeatability_rms_px: float = 3.0,
    maximum_localization_shift_px: float = 20.0,
    minimum_successful_trials: int = 6,
) -> LocalLandmarkValidation:
    """Refine one explicit proposal locally or reject it as unstable.

    Nine deterministic seed positions are tested. This is deliberately not a
    feature matcher: no point outside the proposal neighbourhood can create a
    landmark or a cross-view identity.
    """
    if search_radius_px < 6 or perturbation_px < 1:
        raise ValueError("local landmark search radius/perturbation are too small")
    if maximum_repeatability_rms_px <= 0 or maximum_localization_shift_px <= 0:
        raise ValueError("local landmark validation thresholds must be positive")
    gray = _decode_gray(content)
    height, width = gray.shape
    base_x = proposed_point.x * width
    base_y = proposed_point.y * height
    offsets = [
        (0, 0),
        (-perturbation_px, 0), (perturbation_px, 0),
        (0, -perturbation_px), (0, perturbation_px),
        (-perturbation_px, -perturbation_px), (-perturbation_px, perturbation_px),
        (perturbation_px, -perturbation_px), (perturbation_px, perturbation_px),
    ]
    points = [
        point
        for dx, dy in offsets
        if (point := _refine_one(gray, base_x + dx, base_y + dy, search_radius_px)) is not None
    ]
    if len(points) < minimum_successful_trials:
        return LocalLandmarkValidation(
            physical_landmark_id=physical_landmark_id,
            photo_index=photo_index,
            status="REJECTED",
            proposed_point=proposed_point,
            successful_trials=len(points),
            total_trials=len(offsets),
            diagnostic="Local corner could not be recovered often enough under bounded seed perturbations.",
        )
    array = np.asarray(points, dtype=float)
    refined = np.median(array, axis=0)
    distances = np.linalg.norm(array - refined, axis=1)
    rms = float(np.sqrt(np.mean(np.square(distances))))
    shift = float(np.linalg.norm(refined - np.array([base_x, base_y], dtype=float)))
    if rms > maximum_repeatability_rms_px or shift > maximum_localization_shift_px:
        return LocalLandmarkValidation(
            physical_landmark_id=physical_landmark_id,
            photo_index=photo_index,
            status="REJECTED",
            proposed_point=proposed_point,
            repeatability_rms_px=rms,
            localization_shift_px=shift,
            successful_trials=len(points),
            total_trials=len(offsets),
            diagnostic=(
                f"Local point is unstable or too far from provider proposal: repeatability_rms_px={rms:.6g}, "
                f"localization_shift_px={shift:.6g}."
            ),
        )
    refined_point = NormalizedImagePoint(
        x=min(1.0, max(0.0, float(refined[0]) / width)),
        y=min(1.0, max(0.0, float(refined[1]) / height)),
    )
    return LocalLandmarkValidation(
        physical_landmark_id=physical_landmark_id,
        photo_index=photo_index,
        status="ACCEPTED",
        proposed_point=proposed_point,
        refined_point=refined_point,
        repeatability_rms_px=rms,
        localization_shift_px=shift,
        successful_trials=len(points),
        total_trials=len(offsets),
        diagnostic=(
            f"Stable bounded local refinement from {len(points)}/{len(offsets)} deterministic trials; "
            f"repeatability_rms_px={rms:.6g}, localization_shift_px={shift:.6g}."
        ),
    )
