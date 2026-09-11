"""Minimal relative multi-view reconstruction sidecar.

This module intentionally stops short of camera estimation, SfM, bundle adjustment,
or Scene promotion. It consumes explicit relative camera hypotheses plus explicit
architectural landmark correspondences, validates their Survey provenance, and
triangulates only when the observed parallax makes the result identifiable.

ArchitecturalSurvey is read-only semantic evidence. ArchitecturalScene is not an
input and is never mutated.
"""
from __future__ import annotations

from math import acos, degrees, sqrt
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.survey import ArchitecturalSurvey

from .photo_rectification import NormalizedImagePoint


RelativeReconstructionStatus = Literal["RESOLVED_RELATIVE", "UNRESOLVED"]
_EPS = 1e-12


class RelativePoint3D(BaseModel):
    x: float
    y: float
    z: float


class RelativeVector3D(BaseModel):
    x: float
    y: float
    z: float


class RelativeCameraHypothesis(BaseModel):
    """Explicit calibrated camera hypothesis in an arbitrary relative 3D frame.

    Image points remain in the existing ``x/width, y/height`` coordinate space.
    ``focal_x`` and ``focal_y`` therefore use those same per-axis normalized units
    and are required for real non-square images. ``focal_length`` is retained as
    a backwards-compatible isotropic normalized focal for synthetic/square cases.
    The camera basis follows image convention: ``right`` increases image x,
    ``up`` decreases image y, and ``forward`` points toward positive depth.
    """

    id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    origin: RelativePoint3D
    right: RelativeVector3D
    up: RelativeVector3D
    forward: RelativeVector3D
    focal_length: float | None = Field(default=None, gt=0)
    focal_x: float | None = Field(default=None, gt=0)
    focal_y: float | None = Field(default=None, gt=0)
    principal_x: float = Field(default=0.5, ge=0, le=1)
    principal_y: float = Field(default=0.5, ge=0, le=1)
    source: SourceInfo
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_camera_basis(self) -> "RelativeCameraHypothesis":
        right = _normalize(_vec(self.right))
        up = _normalize(_vec(self.up))
        forward = _normalize(_vec(self.forward))
        if max(abs(_dot(right, up)), abs(_dot(right, forward)), abs(_dot(up, forward))) > 1e-6:
            raise ValueError("relative camera basis vectors must be orthogonal")
        handed = _cross(right, up)
        if _dot(handed, forward) < 1.0 - 1e-6:
            raise ValueError("relative camera basis must be right-handed")
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.USER_PROVIDED, SourceKind.INFERRED}:
            raise ValueError("relative camera source must be observed, user_provided or inferred")
        pair_supplied = self.focal_x is not None or self.focal_y is not None
        if pair_supplied and (self.focal_x is None or self.focal_y is None):
            raise ValueError("relative camera focal_x and focal_y must be supplied together")
        if not pair_supplied and self.focal_length is None:
            raise ValueError("relative camera requires focal_x/focal_y or legacy focal_length")
        return self


class RelativeLandmarkObservation(BaseModel):
    """One explicit 2D observation of a physical architectural landmark."""

    photo_index: int = Field(ge=1)
    observation_id: str = Field(min_length=1)
    point: NormalizedImagePoint
    source: SourceInfo
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_source(self) -> "RelativeLandmarkObservation":
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.INFERRED}:
            raise ValueError("landmark observation source must be observed or inferred")
        return self


class RelativeLandmarkTrack(BaseModel):
    id: str = Field(min_length=1)
    observations: list[RelativeLandmarkObservation] = Field(min_length=2)

    @model_validator(mode="after")
    def validate_unique_photos(self) -> "RelativeLandmarkTrack":
        photos = [item.photo_index for item in self.observations]
        if len(photos) != len(set(photos)):
            raise ValueError("a relative landmark track may contain at most one observation per photo")
        return self


class RelativeLandmarkCandidate(BaseModel):
    landmark_id: str
    status: RelativeReconstructionStatus
    point: RelativePoint3D | None = None
    supporting_photo_indexes: list[int] = Field(default_factory=list)
    parallax_degrees: float = Field(ge=0)
    ray_miss_ratio: float | None = Field(default=None, ge=0)
    reprojection_rms: float | None = Field(default=None, ge=0)
    source: SourceInfo
    diagnostic: str

    @model_validator(mode="after")
    def validate_status(self) -> "RelativeLandmarkCandidate":
        metrics = (self.point, self.ray_miss_ratio, self.reprojection_rms)
        if self.status == "RESOLVED_RELATIVE":
            if any(value is None for value in metrics):
                raise ValueError("resolved relative landmark requires geometry and validation metrics")
            if self.source.kind is not SourceKind.INFERRED:
                raise ValueError("resolved relative landmark source must be inferred")
        elif self.point is not None:
            raise ValueError("unresolved relative landmark must not expose a 3D point")
        return self


class RelativeReconstructionResult(BaseModel):
    status: RelativeReconstructionStatus
    landmarks: list[RelativeLandmarkCandidate] = Field(default_factory=list)
    diagnostic: str


Vec3 = tuple[float, float, float]


def _vec(value: RelativePoint3D | RelativeVector3D) -> Vec3:
    return (value.x, value.y, value.z)


def _add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul(a: Vec3, scalar: float) -> Vec3:
    return (a[0] * scalar, a[1] * scalar, a[2] * scalar)


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _norm(a: Vec3) -> float:
    return sqrt(_dot(a, a))


def _normalize(a: Vec3) -> Vec3:
    length = _norm(a)
    if length <= _EPS:
        raise ValueError("relative camera basis vectors must be non-zero")
    return _mul(a, 1.0 / length)


def _focal_xy(camera: RelativeCameraHypothesis) -> tuple[float, float]:
    if camera.focal_x is not None and camera.focal_y is not None:
        return camera.focal_x, camera.focal_y
    assert camera.focal_length is not None
    return camera.focal_length, camera.focal_length


def _camera_basis(camera: RelativeCameraHypothesis) -> tuple[Vec3, Vec3, Vec3]:
    return _normalize(_vec(camera.right)), _normalize(_vec(camera.up)), _normalize(_vec(camera.forward))


def _observation_ray(camera: RelativeCameraHypothesis, point: NormalizedImagePoint) -> Vec3:
    right, up, forward = _camera_basis(camera)
    focal_x, focal_y = _focal_xy(camera)
    horizontal = (point.x - camera.principal_x) / focal_x
    vertical = (point.y - camera.principal_y) / focal_y
    direction = _add(forward, _add(_mul(right, horizontal), _mul(up, -vertical)))
    return _normalize(direction)


def _closest_points_on_rays(origin_a: Vec3, ray_a: Vec3, origin_b: Vec3, ray_b: Vec3) -> tuple[Vec3, Vec3] | None:
    w0 = _sub(origin_a, origin_b)
    b = _dot(ray_a, ray_b)
    d = _dot(ray_a, w0)
    e = _dot(ray_b, w0)
    denominator = 1.0 - b * b
    if denominator <= _EPS:
        return None
    distance_a = (b * e - d) / denominator
    distance_b = (e - b * d) / denominator
    if distance_a <= 0 or distance_b <= 0:
        return None
    return _add(origin_a, _mul(ray_a, distance_a)), _add(origin_b, _mul(ray_b, distance_b))


def _project(camera: RelativeCameraHypothesis, point: Vec3) -> NormalizedImagePoint | None:
    right, up, forward = _camera_basis(camera)
    focal_x, focal_y = _focal_xy(camera)
    relative = _sub(point, _vec(camera.origin))
    depth = _dot(relative, forward)
    if depth <= _EPS:
        return None
    x = camera.principal_x + focal_x * _dot(relative, right) / depth
    y = camera.principal_y - focal_y * _dot(relative, up) / depth
    if not 0.0 <= x <= 1.0 or not 0.0 <= y <= 1.0:
        return None
    return NormalizedImagePoint(x=x, y=y)


def _validate_provenance(
    survey: ArchitecturalSurvey,
    cameras: list[RelativeCameraHypothesis],
    tracks: list[RelativeLandmarkTrack],
) -> None:
    camera_photos = [camera.photo_index for camera in cameras]
    if len(camera_photos) != len(set(camera_photos)):
        raise ValueError("relative camera hypotheses must reference unique photos")
    known_photos = {photo.photo_index for photo in survey.photos}
    observations = {observation.id: observation for observation in survey.observations}
    for camera in cameras:
        if camera.photo_index not in known_photos:
            raise ValueError(f"relative camera {camera.id!r} references unknown photo {camera.photo_index}")
    track_ids = [track.id for track in tracks]
    if len(track_ids) != len(set(track_ids)):
        raise ValueError("relative landmark track ids must be unique")
    for track in tracks:
        for item in track.observations:
            if item.photo_index not in camera_photos:
                raise ValueError(f"track {track.id!r} references photo {item.photo_index} without a camera hypothesis")
            observation = observations.get(item.observation_id)
            if observation is None:
                raise ValueError(f"track {track.id!r} references unknown Survey observation {item.observation_id!r}")
            evidence_photos = {evidence.photo_index for evidence in observation.evidence}
            if item.photo_index not in evidence_photos:
                raise ValueError(
                    f"track {track.id!r} observation {item.observation_id!r} is not backed by Survey evidence on photo {item.photo_index}"
                )


def reconstruct_relative_landmarks(
    survey: ArchitecturalSurvey,
    cameras: list[RelativeCameraHypothesis],
    tracks: list[RelativeLandmarkTrack],
    *,
    minimum_parallax_degrees: float = 1.0,
    maximum_ray_miss_ratio: float = 0.02,
    maximum_reprojection_rms: float = 0.01,
) -> RelativeReconstructionResult:
    """Triangulate explicit architectural tracks in a relative camera frame.

    The best camera pair is selected deterministically by maximum parallax. A
    landmark is returned only when parallax, ray agreement and reprojection all
    pass conservative thresholds; otherwise it is ``UNRESOLVED`` with no 3D point.
    """
    if minimum_parallax_degrees <= 0:
        raise ValueError("minimum_parallax_degrees must be positive")
    if maximum_ray_miss_ratio <= 0 or maximum_reprojection_rms <= 0:
        raise ValueError("relative reconstruction thresholds must be positive")
    _validate_provenance(survey, cameras, tracks)
    camera_by_photo = {camera.photo_index: camera for camera in cameras}
    candidates: list[RelativeLandmarkCandidate] = []

    for track in sorted(tracks, key=lambda item: item.id):
        observations = sorted(track.observations, key=lambda item: item.photo_index)
        ray_records = [
            (item, camera_by_photo[item.photo_index], _observation_ray(camera_by_photo[item.photo_index], item.point))
            for item in observations
        ]
        pair_options: list[tuple[float, int, int, int, int]] = []
        for first in range(len(ray_records)):
            for second in range(first + 1, len(ray_records)):
                dot_value = max(-1.0, min(1.0, _dot(ray_records[first][2], ray_records[second][2])))
                angle = degrees(acos(dot_value))
                pair_options.append((angle, -ray_records[first][0].photo_index, -ray_records[second][0].photo_index, first, second))
        pair_options.sort(reverse=True)
        best_angle, _, _, first, second = pair_options[0]
        item_a, camera_a, ray_a = ray_records[first]
        item_b, camera_b, ray_b = ray_records[second]
        baseline = _norm(_sub(_vec(camera_a.origin), _vec(camera_b.origin)))
        source_confidence = min(
            [item.source.confidence for item in observations]
            + [camera_by_photo[item.photo_index].source.confidence for item in observations]
        )

        if baseline <= _EPS or best_angle < minimum_parallax_degrees:
            candidates.append(RelativeLandmarkCandidate(
                landmark_id=track.id,
                status="UNRESOLVED",
                supporting_photo_indexes=[item.photo_index for item in observations],
                parallax_degrees=best_angle,
                source=SourceInfo(kind=SourceKind.INFERRED, confidence=0.0),
                diagnostic=(
                    f"Insufficient relative baseline/parallax: baseline={baseline:.6g}, "
                    f"parallax={best_angle:.6g} deg."
                ),
            ))
            continue

        closest = _closest_points_on_rays(_vec(camera_a.origin), ray_a, _vec(camera_b.origin), ray_b)
        if closest is None:
            candidates.append(RelativeLandmarkCandidate(
                landmark_id=track.id,
                status="UNRESOLVED",
                supporting_photo_indexes=[item.photo_index for item in observations],
                parallax_degrees=best_angle,
                source=SourceInfo(kind=SourceKind.INFERRED, confidence=0.0),
                diagnostic="Triangulation is not physically identifiable in front of both cameras.",
            ))
            continue

        point_a, point_b = closest
        midpoint = _mul(_add(point_a, point_b), 0.5)
        ray_miss_ratio = _norm(_sub(point_a, point_b)) / baseline
        squared_errors: list[float] = []
        projection_failed = False
        for item in observations:
            projected = _project(camera_by_photo[item.photo_index], midpoint)
            if projected is None:
                projection_failed = True
                break
            squared_errors.append((projected.x - item.point.x) ** 2 + (projected.y - item.point.y) ** 2)
        reprojection_rms = sqrt(sum(squared_errors) / len(squared_errors)) if squared_errors else None

        if (
            projection_failed
            or ray_miss_ratio > maximum_ray_miss_ratio
            or reprojection_rms is None
            or reprojection_rms > maximum_reprojection_rms
        ):
            candidates.append(RelativeLandmarkCandidate(
                landmark_id=track.id,
                status="UNRESOLVED",
                supporting_photo_indexes=[item.photo_index for item in observations],
                parallax_degrees=best_angle,
                ray_miss_ratio=ray_miss_ratio,
                reprojection_rms=reprojection_rms,
                source=SourceInfo(kind=SourceKind.INFERRED, confidence=0.0),
                diagnostic=(
                    "Candidate failed geometric consistency: "
                    f"ray_miss_ratio={ray_miss_ratio:.6g}, reprojection_rms={reprojection_rms}."
                ),
            ))
            continue

        candidates.append(RelativeLandmarkCandidate(
            landmark_id=track.id,
            status="RESOLVED_RELATIVE",
            point=RelativePoint3D(x=midpoint[0], y=midpoint[1], z=midpoint[2]),
            supporting_photo_indexes=[item.photo_index for item in observations],
            parallax_degrees=best_angle,
            ray_miss_ratio=ray_miss_ratio,
            reprojection_rms=reprojection_rms,
            source=SourceInfo(kind=SourceKind.INFERRED, confidence=source_confidence),
            diagnostic=(
                f"Resolved from {len(observations)} explicit views; best parallax={best_angle:.6g} deg; "
                f"ray_miss_ratio={ray_miss_ratio:.6g}; reprojection_rms={reprojection_rms:.6g}."
            ),
        ))

    resolved = [item for item in candidates if item.status == "RESOLVED_RELATIVE"]
    status: RelativeReconstructionStatus = "RESOLVED_RELATIVE" if resolved else "UNRESOLVED"
    return RelativeReconstructionResult(
        status=status,
        landmarks=candidates,
        diagnostic=f"Resolved {len(resolved)} of {len(candidates)} explicit landmark track(s).",
    )
