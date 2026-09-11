"""Bounded calibrated two-view camera estimation for explicit architectural tracks.

This is intentionally not self-calibration or SfM. Both photo intrinsics must be
explicitly supplied. The deterministic eight-point essential-matrix solution is
accepted only when the correspondence system has full support, one cheirality
solution is distinguishable, and useful parallax remains. Otherwise the result is
UNRESOLVED and exposes no camera hypotheses.
"""
from __future__ import annotations

from math import acos, degrees
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.survey import ArchitecturalSurvey

from .relative_multiview import (
    RelativeCameraHypothesis,
    RelativeLandmarkTrack,
    RelativePoint3D,
    RelativeVector3D,
)


RelativeCameraEstimationStatus = Literal["RESOLVED_RELATIVE", "UNRESOLVED"]
_EPS = 1e-12


class CalibratedPhotoIntrinsics(BaseModel):
    """Explicit fixed pinhole intrinsics in normalized-image units."""

    id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    focal_length: float = Field(gt=0)
    principal_x: float = Field(default=0.5, ge=0, le=1)
    principal_y: float = Field(default=0.5, ge=0, le=1)
    source: SourceInfo
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_source(self) -> "CalibratedPhotoIntrinsics":
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.USER_PROVIDED, SourceKind.INFERRED}:
            raise ValueError("calibrated photo intrinsics must have traceable observed, user_provided or inferred provenance")
        return self


class RelativeCameraEstimationResult(BaseModel):
    status: RelativeCameraEstimationStatus
    cameras: list[RelativeCameraHypothesis] = Field(default_factory=list)
    supporting_landmark_ids: list[str] = Field(default_factory=list)
    epipolar_rms: float | None = Field(default=None, ge=0)
    positive_depth_fraction: float | None = Field(default=None, ge=0, le=1)
    median_parallax_degrees: float | None = Field(default=None, ge=0)
    diagnostic: str

    @model_validator(mode="after")
    def validate_status(self) -> "RelativeCameraEstimationResult":
        if self.status == "RESOLVED_RELATIVE":
            if len(self.cameras) != 2:
                raise ValueError("resolved relative camera estimation requires exactly two cameras")
            if self.epipolar_rms is None or self.positive_depth_fraction is None or self.median_parallax_degrees is None:
                raise ValueError("resolved relative camera estimation requires validation metrics")
        elif self.cameras:
            raise ValueError("unresolved relative camera estimation must not expose camera hypotheses")
        return self


def _unresolved(ids: list[str], diagnostic: str, *, epipolar_rms: float | None = None) -> RelativeCameraEstimationResult:
    return RelativeCameraEstimationResult(
        status="UNRESOLVED",
        supporting_landmark_ids=ids,
        epipolar_rms=epipolar_rms,
        diagnostic=diagnostic,
    )


def _normalized_camera_point(item, intrinsics: CalibratedPhotoIntrinsics) -> np.ndarray:
    return np.array(
        [
            (item.point.x - intrinsics.principal_x) / intrinsics.focal_length,
            (intrinsics.principal_y - item.point.y) / intrinsics.focal_length,
            1.0,
        ],
        dtype=float,
    )


def _triangulate(p1: np.ndarray, p2: np.ndarray, rotation: np.ndarray, translation: np.ndarray) -> np.ndarray | None:
    projection_1 = np.column_stack((np.eye(3), np.zeros(3)))
    projection_2 = np.column_stack((rotation, translation))
    matrix = np.vstack(
        (
            p1[0] * projection_1[2] - projection_1[0],
            p1[1] * projection_1[2] - projection_1[1],
            p2[0] * projection_2[2] - projection_2[0],
            p2[1] * projection_2[2] - projection_2[1],
        )
    )
    _, _, vh = np.linalg.svd(matrix)
    homogeneous = vh[-1]
    if abs(homogeneous[3]) <= _EPS:
        return None
    return homogeneous[:3] / homogeneous[3]


def _candidate_geometry(
    points_1: list[np.ndarray],
    points_2: list[np.ndarray],
    rotation: np.ndarray,
    translation: np.ndarray,
) -> tuple[int, list[float]]:
    center_2 = -(rotation.T @ translation)
    positive = 0
    parallaxes: list[float] = []
    for first, second in zip(points_1, points_2, strict=True):
        point = _triangulate(first, second, rotation, translation)
        if point is None:
            continue
        depth_1 = point[2]
        point_2 = rotation @ point + translation
        depth_2 = point_2[2]
        if depth_1 <= _EPS or depth_2 <= _EPS:
            continue
        positive += 1
        ray_1 = point / np.linalg.norm(point)
        ray_2_vector = point - center_2
        ray_2 = ray_2_vector / np.linalg.norm(ray_2_vector)
        cosine = float(np.clip(np.dot(ray_1, ray_2), -1.0, 1.0))
        parallaxes.append(degrees(acos(cosine)))
    return positive, parallaxes


def _camera_from_pose(
    photo_index: int,
    intrinsics: CalibratedPhotoIntrinsics,
    rotation_world_to_camera: np.ndarray,
    translation_world_to_camera: np.ndarray,
    confidence: float,
) -> RelativeCameraHypothesis:
    center = -(rotation_world_to_camera.T @ translation_world_to_camera)
    return RelativeCameraHypothesis(
        id=f"relative-camera-photo-{photo_index}",
        photo_index=photo_index,
        origin=RelativePoint3D(x=float(center[0]), y=float(center[1]), z=float(center[2])),
        right=RelativeVector3D(
            x=float(rotation_world_to_camera[0, 0]),
            y=float(rotation_world_to_camera[0, 1]),
            z=float(rotation_world_to_camera[0, 2]),
        ),
        up=RelativeVector3D(
            x=float(rotation_world_to_camera[1, 0]),
            y=float(rotation_world_to_camera[1, 1]),
            z=float(rotation_world_to_camera[1, 2]),
        ),
        forward=RelativeVector3D(
            x=float(rotation_world_to_camera[2, 0]),
            y=float(rotation_world_to_camera[2, 1]),
            z=float(rotation_world_to_camera[2, 2]),
        ),
        focal_length=intrinsics.focal_length,
        principal_x=intrinsics.principal_x,
        principal_y=intrinsics.principal_y,
        source=SourceInfo(kind=SourceKind.INFERRED, confidence=confidence),
        statement="Deterministic calibrated two-view relative pose from explicit architectural landmark tracks.",
    )


def estimate_relative_camera_pair(
    survey: ArchitecturalSurvey,
    intrinsics: list[CalibratedPhotoIntrinsics],
    tracks: list[RelativeLandmarkTrack],
    *,
    first_photo_index: int,
    second_photo_index: int,
    minimum_tracks: int = 8,
    minimum_parallax_degrees: float = 1.0,
    maximum_epipolar_rms: float = 0.01,
) -> RelativeCameraEstimationResult:
    """Estimate one calibrated relative camera pair or return UNRESOLVED.

    Camera 1 defines the arbitrary relative frame. Translation magnitude is fixed
    to one relative unit; no metric scale is inferred.
    """
    if first_photo_index == second_photo_index:
        raise ValueError("relative camera estimation requires two distinct photos")
    if minimum_tracks < 8:
        raise ValueError("calibrated eight-point estimation requires at least eight tracks")
    if minimum_parallax_degrees <= 0 or maximum_epipolar_rms <= 0:
        raise ValueError("camera estimation thresholds must be positive")

    known_photos = {photo.photo_index for photo in survey.photos}
    if first_photo_index not in known_photos or second_photo_index not in known_photos:
        raise ValueError("relative camera estimation references a photo absent from Survey")
    intrinsics_by_photo = {item.photo_index: item for item in intrinsics}
    if len(intrinsics_by_photo) != len(intrinsics):
        raise ValueError("calibrated photo intrinsics must reference unique photos")
    if first_photo_index not in intrinsics_by_photo or second_photo_index not in intrinsics_by_photo:
        return _unresolved([], "Explicit calibrated intrinsics are required for both photos; focal self-calibration is outside BH-237.")

    first_intrinsics = intrinsics_by_photo[first_photo_index]
    second_intrinsics = intrinsics_by_photo[second_photo_index]
    usable: list[tuple[str, object, object]] = []
    for track in sorted(tracks, key=lambda item: item.id):
        by_photo = {item.photo_index: item for item in track.observations}
        if first_photo_index in by_photo and second_photo_index in by_photo:
            usable.append((track.id, by_photo[first_photo_index], by_photo[second_photo_index]))
    ids = [item[0] for item in usable]
    if len(usable) < minimum_tracks:
        return _unresolved(ids, f"Only {len(usable)} explicit cross-view track(s); require at least {minimum_tracks} for calibrated pose estimation.")

    points_1 = [_normalized_camera_point(item[1], first_intrinsics) for item in usable]
    points_2 = [_normalized_camera_point(item[2], second_intrinsics) for item in usable]
    xy_1 = np.array([[point[0], point[1]] for point in points_1])
    xy_2 = np.array([[point[0], point[1]] for point in points_2])
    if np.linalg.matrix_rank(xy_1 - xy_1.mean(axis=0)) < 2 or np.linalg.matrix_rank(xy_2 - xy_2.mean(axis=0)) < 2:
        return _unresolved(ids, "Landmark image geometry is degenerate: points do not span two image dimensions.")

    design = np.array(
        [
            [p2[0] * p1[0], p2[0] * p1[1], p2[0], p2[1] * p1[0], p2[1] * p1[1], p2[1], p1[0], p1[1], 1.0]
            for p1, p2 in zip(points_1, points_2, strict=True)
        ],
        dtype=float,
    )
    if np.linalg.matrix_rank(design, tol=1e-10) < 8:
        return _unresolved(ids, "Two-view correspondence system is rank-deficient; relative pose is not identifiable.")

    _, _, vh = np.linalg.svd(design)
    essential_raw = vh[-1].reshape(3, 3)
    u, singular, vt = np.linalg.svd(essential_raw)
    if np.linalg.det(u) < 0:
        u[:, -1] *= -1
    if np.linalg.det(vt) < 0:
        vt[-1, :] *= -1
    sigma = float((singular[0] + singular[1]) / 2.0)
    essential = u @ np.diag([sigma, sigma, 0.0]) @ vt

    residuals = [float(p2 @ essential @ p1) for p1, p2 in zip(points_1, points_2, strict=True)]
    epipolar_rms = float(np.sqrt(np.mean(np.square(residuals))))
    if not np.isfinite(epipolar_rms) or epipolar_rms > maximum_epipolar_rms:
        return _unresolved(ids, "Calibrated correspondences do not support a coherent essential matrix within the reprojection gate.", epipolar_rms=epipolar_rms)

    u, _, vt = np.linalg.svd(essential)
    if np.linalg.det(u) < 0:
        u[:, -1] *= -1
    if np.linalg.det(vt) < 0:
        vt[-1, :] *= -1
    w = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    rotations = [u @ w @ vt, u @ w.T @ vt]
    rotations = [rotation if np.linalg.det(rotation) > 0 else -rotation for rotation in rotations]
    direction = u[:, 2]
    candidates: list[tuple[int, float, int, np.ndarray, np.ndarray, list[float]]] = []
    candidate_index = 0
    for rotation in rotations:
        for translation in (direction, -direction):
            positive, parallaxes = _candidate_geometry(points_1, points_2, rotation, translation)
            median_parallax = float(np.median(parallaxes)) if parallaxes else 0.0
            candidates.append((positive, median_parallax, -candidate_index, rotation, translation, parallaxes))
            candidate_index += 1
    candidates.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    best = candidates[0]
    second = candidates[1]
    required_positive = max(minimum_tracks, int(np.ceil(0.8 * len(usable))))
    if best[0] < required_positive or best[0] == second[0]:
        return _unresolved(ids, "Cheirality does not identify one relative camera pose strongly enough.", epipolar_rms=epipolar_rms)
    if best[1] < minimum_parallax_degrees:
        return _unresolved(ids, f"Relative camera parallax is insufficient ({best[1]:.6g} deg).", epipolar_rms=epipolar_rms)

    confidence_values = [first_intrinsics.source.confidence, second_intrinsics.source.confidence]
    for _, first, second_item in usable:
        confidence_values.extend([first.source.confidence, second_item.source.confidence])
    confidence = min(confidence_values)
    identity = np.eye(3)
    zero = np.zeros(3)
    cameras = [
        _camera_from_pose(first_photo_index, first_intrinsics, identity, zero, confidence),
        _camera_from_pose(second_photo_index, second_intrinsics, best[3], best[4], confidence),
    ]
    return RelativeCameraEstimationResult(
        status="RESOLVED_RELATIVE",
        cameras=cameras,
        supporting_landmark_ids=ids,
        epipolar_rms=epipolar_rms,
        positive_depth_fraction=best[0] / len(usable),
        median_parallax_degrees=best[1],
        diagnostic=(
            f"Resolved calibrated relative pose from {len(usable)} explicit tracks; "
            "translation scale remains arbitrary and metric scale is intentionally absent."
        ),
    )
