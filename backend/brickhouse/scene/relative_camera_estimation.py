"""Bounded calibrated two-view camera estimation for explicit architectural tracks.

This is intentionally not self-calibration or SfM. Both photo intrinsics must be
explicitly supplied. Real-photo calibration is expressed in pixels and converted
to a documented square-canvas normalized coordinate space before a BH-236 camera
hypothesis is exposed. The legacy normalized scalar contract remains available for
existing synthetic/square tests only.
"""
from __future__ import annotations

from math import acos, degrees
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.survey import ArchitecturalSurvey

from .photo_rectification import NormalizedImagePoint
from .relative_multiview import (
    RelativeCameraHypothesis,
    RelativeLandmarkObservation,
    RelativeLandmarkTrack,
    RelativePoint3D,
    RelativeVector3D,
)


RelativeCameraEstimationStatus = Literal["RESOLVED_RELATIVE", "UNRESOLVED"]
CameraIntrinsicSpace = Literal["legacy_normalized", "pixel"]
_EPS = 1e-12
_PIXEL_FOCAL_REL_TOL = 0.02


class CalibratedPhotoIntrinsics(BaseModel):
    """Explicit fixed pinhole intrinsics.

    ``legacy_normalized`` preserves BH-237's original synthetic contract where x,
    y and one focal length already share one isotropic normalized unit.

    ``pixel`` is the real-photo contract. The source image still stores 2D points
    as x/width and y/height, but camera rays are formed in pixels using width,
    height, fx, fy, cx and cy. Before a BH-236 camera is returned, those image
    points are converted to a centered square canvas of side max(width, height),
    yielding one isotropic normalized unit. Because RelativeCameraHypothesis still
    has one scalar focal, pixel fx/fy must agree within 2%; otherwise camera output
    remains UNRESOLVED rather than silently distorting the image.
    """

    id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    coordinate_space: CameraIntrinsicSpace = "legacy_normalized"
    focal_length: float | None = Field(default=None, gt=0)
    principal_x: float = Field(default=0.5, ge=0, le=1)
    principal_y: float = Field(default=0.5, ge=0, le=1)
    image_width_px: int | None = Field(default=None, gt=0)
    image_height_px: int | None = Field(default=None, gt=0)
    focal_x_px: float | None = Field(default=None, gt=0)
    focal_y_px: float | None = Field(default=None, gt=0)
    principal_x_px: float | None = None
    principal_y_px: float | None = None
    source: SourceInfo
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_source_and_space(self) -> "CalibratedPhotoIntrinsics":
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.USER_PROVIDED, SourceKind.INFERRED}:
            raise ValueError("calibrated photo intrinsics must have traceable observed, user_provided or inferred provenance")
        if self.coordinate_space == "legacy_normalized":
            if self.focal_length is None:
                raise ValueError("legacy normalized intrinsics require focal_length")
            return self
        required = {
            "image_width_px": self.image_width_px,
            "image_height_px": self.image_height_px,
            "focal_x_px": self.focal_x_px,
            "focal_y_px": self.focal_y_px,
            "principal_x_px": self.principal_x_px,
            "principal_y_px": self.principal_y_px,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise ValueError(f"pixel intrinsics require {', '.join(missing)}")
        assert self.image_width_px is not None and self.image_height_px is not None
        assert self.principal_x_px is not None and self.principal_y_px is not None
        if not 0.0 <= self.principal_x_px <= self.image_width_px or not 0.0 <= self.principal_y_px <= self.image_height_px:
            raise ValueError("pixel principal point must lie inside the source image")
        return self


class RelativeCameraEstimationResult(BaseModel):
    status: RelativeCameraEstimationStatus
    cameras: list[RelativeCameraHypothesis] = Field(default_factory=list)
    supporting_landmark_ids: list[str] = Field(default_factory=list)
    bh236_tracks: list[RelativeLandmarkTrack] = Field(default_factory=list)
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
            if not self.bh236_tracks:
                raise ValueError("resolved relative camera estimation requires tracks expressed in the returned camera coordinate space")
        elif self.cameras or self.bh236_tracks:
            raise ValueError("unresolved relative camera estimation must not expose cameras or BH-236 tracks")
        return self


def _unresolved(ids: list[str], diagnostic: str, *, epipolar_rms: float | None = None) -> RelativeCameraEstimationResult:
    return RelativeCameraEstimationResult(
        status="UNRESOLVED",
        supporting_landmark_ids=ids,
        epipolar_rms=epipolar_rms,
        diagnostic=diagnostic,
    )


def _pixel_values(intrinsics: CalibratedPhotoIntrinsics) -> tuple[float, float, float, float, float, float]:
    assert intrinsics.image_width_px is not None and intrinsics.image_height_px is not None
    assert intrinsics.focal_x_px is not None and intrinsics.focal_y_px is not None
    assert intrinsics.principal_x_px is not None and intrinsics.principal_y_px is not None
    return (
        float(intrinsics.image_width_px),
        float(intrinsics.image_height_px),
        intrinsics.focal_x_px,
        intrinsics.focal_y_px,
        intrinsics.principal_x_px,
        intrinsics.principal_y_px,
    )


def _normalized_camera_point(item, intrinsics: CalibratedPhotoIntrinsics) -> np.ndarray:
    if intrinsics.coordinate_space == "legacy_normalized":
        assert intrinsics.focal_length is not None
        return np.array(
            [
                (item.point.x - intrinsics.principal_x) / intrinsics.focal_length,
                (intrinsics.principal_y - item.point.y) / intrinsics.focal_length,
                1.0,
            ],
            dtype=float,
        )
    width, height, fx, fy, cx, cy = _pixel_values(intrinsics)
    u = item.point.x * width
    v = item.point.y * height
    return np.array([(u - cx) / fx, (cy - v) / fy, 1.0], dtype=float)


def _square_canvas_point(point: NormalizedImagePoint, intrinsics: CalibratedPhotoIntrinsics) -> NormalizedImagePoint:
    if intrinsics.coordinate_space == "legacy_normalized":
        return point
    width, height, _, _, _, _ = _pixel_values(intrinsics)
    side = max(width, height)
    offset_x = (side - width) / 2.0
    offset_y = (side - height) / 2.0
    return NormalizedImagePoint(
        x=(point.x * width + offset_x) / side,
        y=(point.y * height + offset_y) / side,
    )


def _camera_scalar_intrinsics(intrinsics: CalibratedPhotoIntrinsics) -> tuple[float, float, float] | None:
    if intrinsics.coordinate_space == "legacy_normalized":
        assert intrinsics.focal_length is not None
        return intrinsics.focal_length, intrinsics.principal_x, intrinsics.principal_y
    width, height, fx, fy, cx, cy = _pixel_values(intrinsics)
    mean_focal = (fx + fy) / 2.0
    if abs(fx - fy) / mean_focal > _PIXEL_FOCAL_REL_TOL:
        return None
    side = max(width, height)
    offset_x = (side - width) / 2.0
    offset_y = (side - height) / 2.0
    return mean_focal / side, (cx + offset_x) / side, (cy + offset_y) / side


def _tracks_for_bh236(
    tracks: list[RelativeLandmarkTrack],
    intrinsics_by_photo: dict[int, CalibratedPhotoIntrinsics],
) -> list[RelativeLandmarkTrack]:
    result: list[RelativeLandmarkTrack] = []
    for track in tracks:
        observations: list[RelativeLandmarkObservation] = []
        for item in track.observations:
            intrinsics = intrinsics_by_photo.get(item.photo_index)
            point = _square_canvas_point(item.point, intrinsics) if intrinsics is not None else item.point
            observations.append(
                RelativeLandmarkObservation(
                    photo_index=item.photo_index,
                    observation_id=item.observation_id,
                    point=point,
                    source=item.source,
                    statement=item.statement,
                )
            )
        result.append(RelativeLandmarkTrack(id=track.id, observations=observations))
    return result


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


def _candidate_geometry(points_1, points_2, rotation, translation) -> tuple[int, list[float]]:
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


def _camera_from_pose(photo_index, intrinsics, rotation_world_to_camera, translation_world_to_camera, confidence):
    scalar = _camera_scalar_intrinsics(intrinsics)
    if scalar is None:
        raise ValueError("pixel focal x/y cannot be represented by BH-236 scalar focal contract")
    focal_length, principal_x, principal_y = scalar
    center = -(rotation_world_to_camera.T @ translation_world_to_camera)
    return RelativeCameraHypothesis(
        id=f"relative-camera-photo-{photo_index}",
        photo_index=photo_index,
        origin=RelativePoint3D(x=float(center[0]), y=float(center[1]), z=float(center[2])),
        right=RelativeVector3D(x=float(rotation_world_to_camera[0, 0]), y=float(rotation_world_to_camera[0, 1]), z=float(rotation_world_to_camera[0, 2])),
        up=RelativeVector3D(x=float(rotation_world_to_camera[1, 0]), y=float(rotation_world_to_camera[1, 1]), z=float(rotation_world_to_camera[1, 2])),
        forward=RelativeVector3D(x=float(rotation_world_to_camera[2, 0]), y=float(rotation_world_to_camera[2, 1]), z=float(rotation_world_to_camera[2, 2])),
        focal_length=focal_length,
        principal_x=principal_x,
        principal_y=principal_y,
        source=SourceInfo(kind=SourceKind.INFERRED, confidence=confidence),
        statement="Deterministic calibrated two-view relative pose in an isotropic normalized image space.",
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
    """Estimate one calibrated relative camera pair or return UNRESOLVED."""
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
    for item in (first_intrinsics, second_intrinsics):
        if item.coordinate_space == "pixel" and _camera_scalar_intrinsics(item) is None:
            return _unresolved([], "Pixel intrinsics have materially different fx/fy; BH-236 scalar-focal camera output cannot represent them without distortion.")

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

    design = np.array([
        [p2[0] * p1[0], p2[0] * p1[1], p2[0], p2[1] * p1[0], p2[1] * p1[1], p2[1], p1[0], p1[1], 1.0]
        for p1, p2 in zip(points_1, points_2, strict=True)
    ], dtype=float)
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
    candidates = []
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
        bh236_tracks=_tracks_for_bh236(tracks, intrinsics_by_photo),
        epipolar_rms=epipolar_rms,
        positive_depth_fraction=best[0] / len(usable),
        median_parallax_degrees=best[1],
        diagnostic=(
            f"Resolved calibrated relative pose from {len(usable)} explicit tracks; "
            "translation scale remains arbitrary and metric scale is intentionally absent."
        ),
    )
