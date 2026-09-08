"""Perspective-safe planar rectification for photo geometry scale evidence.

The transform is an inference sidecar. It does not change ArchitecturalSurvey and
never creates a known measurement. Four explicit points identify the photographed
plane and are mapped projectively to a unit rectangle.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.survey import NormalizedImageRegion

from .photo_scale_cues import PhotoGeometryAnnotation

_EPS = 1e-10


class NormalizedImagePoint(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class NormalizedImageQuadrilateral(BaseModel):
    """Convex plane corners in clockwise order: TL, TR, BR, BL."""

    top_left: NormalizedImagePoint
    top_right: NormalizedImagePoint
    bottom_right: NormalizedImagePoint
    bottom_left: NormalizedImagePoint

    def points(self) -> list[NormalizedImagePoint]:
        return [self.top_left, self.top_right, self.bottom_right, self.bottom_left]

    @model_validator(mode="after")
    def validate_convex_clockwise_order(self) -> "NormalizedImageQuadrilateral":
        points = self.points()
        crosses = []
        for index in range(4):
            a = points[index]
            b = points[(index + 1) % 4]
            c = points[(index + 2) % 4]
            crosses.append((b.x - a.x) * (c.y - b.y) - (b.y - a.y) * (c.x - b.x))
        if any(abs(value) <= _EPS for value in crosses):
            raise ValueError("rectification quadrilateral must be non-degenerate")
        if not (all(value > 0 for value in crosses) or all(value < 0 for value in crosses)):
            raise ValueError("rectification quadrilateral must be convex and consistently ordered")
        return self


class PlanarPhotoRectification(BaseModel):
    id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    source_quad: NormalizedImageQuadrilateral
    source: SourceInfo
    statement: str = Field(min_length=1)
    source_coordinate_space_id: str = Field(default="image", min_length=1)

    @model_validator(mode="after")
    def validate_source(self) -> "PlanarPhotoRectification":
        if self.source.kind not in {SourceKind.OBSERVED, SourceKind.INFERRED}:
            raise ValueError("photo rectification source.kind must be observed or inferred")
        return self


def _solve_linear_system(matrix: list[list[float]], values: list[float]) -> list[float]:
    """Solve a small dense system with partial-pivot Gaussian elimination."""
    n = len(values)
    augmented = [list(matrix[row]) + [values[row]] for row in range(n)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(augmented[row][col]))
        if abs(augmented[pivot][col]) <= _EPS:
            raise ValueError("rectification quadrilateral does not define a stable projective transform")
        augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        scale = augmented[col][col]
        augmented[col] = [value / scale for value in augmented[col]]
        for row in range(n):
            if row == col:
                continue
            factor = augmented[row][col]
            if abs(factor) <= _EPS:
                continue
            augmented[row] = [
                augmented[row][idx] - factor * augmented[col][idx]
                for idx in range(n + 1)
            ]
    return [augmented[row][-1] for row in range(n)]


def _homography(rectification: PlanarPhotoRectification) -> tuple[float, ...]:
    source = rectification.source_quad.points()
    target = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    matrix: list[list[float]] = []
    values: list[float] = []
    for point, (u, v) in zip(source, target, strict=True):
        x, y = point.x, point.y
        matrix.append([x, y, 1.0, 0.0, 0.0, 0.0, -u * x, -u * y])
        values.append(u)
        matrix.append([0.0, 0.0, 0.0, x, y, 1.0, -v * x, -v * y])
        values.append(v)
    return tuple(_solve_linear_system(matrix, values)) + (1.0,)


def rectify_point(
    rectification: PlanarPhotoRectification,
    point: NormalizedImagePoint,
) -> NormalizedImagePoint:
    h = _homography(rectification)
    denominator = h[6] * point.x + h[7] * point.y + h[8]
    if abs(denominator) <= _EPS:
        raise ValueError("point maps to infinity under photo rectification")
    u = (h[0] * point.x + h[1] * point.y + h[2]) / denominator
    v = (h[3] * point.x + h[4] * point.y + h[5]) / denominator
    tolerance = 1e-8
    if not -tolerance <= u <= 1 + tolerance or not -tolerance <= v <= 1 + tolerance:
        raise ValueError("point lies outside the rectified source plane")
    return NormalizedImagePoint(x=min(1.0, max(0.0, u)), y=min(1.0, max(0.0, v)))


def _point_inside_convex_quad(point: NormalizedImagePoint, quad: NormalizedImageQuadrilateral) -> bool:
    corners = quad.points()
    signs: list[float] = []
    for index in range(4):
        a = corners[index]
        b = corners[(index + 1) % 4]
        signs.append((b.x - a.x) * (point.y - a.y) - (b.y - a.y) * (point.x - a.x))
    return all(value >= -_EPS for value in signs) or all(value <= _EPS for value in signs)


def rectify_photo_geometry_annotation(
    rectification: PlanarPhotoRectification,
    annotation: PhotoGeometryAnnotation,
) -> PhotoGeometryAnnotation:
    """Project an original-space annotation into the rectified unit plane."""
    if annotation.photo_index != rectification.photo_index:
        raise ValueError("photo geometry annotation and rectification must reference the same photo")
    if annotation.coordinate_space_id != rectification.source_coordinate_space_id:
        raise ValueError("photo geometry annotation is not in the rectification source coordinate space")

    corners = [
        NormalizedImagePoint(x=annotation.region.x0, y=annotation.region.y0),
        NormalizedImagePoint(x=annotation.region.x1, y=annotation.region.y0),
        NormalizedImagePoint(x=annotation.region.x1, y=annotation.region.y1),
        NormalizedImagePoint(x=annotation.region.x0, y=annotation.region.y1),
    ]
    if not all(_point_inside_convex_quad(point, rectification.source_quad) for point in corners):
        raise ValueError("photo geometry annotation lies outside the rectification source plane")

    mapped = [rectify_point(rectification, point) for point in corners]
    xs = [point.x for point in mapped]
    ys = [point.y for point in mapped]
    return PhotoGeometryAnnotation(
        id=f"{annotation.id}@{rectification.id}",
        observation_id=annotation.observation_id,
        photo_index=annotation.photo_index,
        region=NormalizedImageRegion(x0=min(xs), y0=min(ys), x1=max(xs), y1=max(ys)),
        source=SourceInfo(
            kind=SourceKind.INFERRED,
            confidence=min(annotation.source.confidence, rectification.source.confidence),
        ),
        statement=f"{annotation.statement} Rectified by {rectification.id}: {rectification.statement}",
        coordinate_space_id=rectification.id,
    )


def rectified_plane_reference_annotation(
    rectification: PlanarPhotoRectification,
    *,
    annotation_id: str,
    observation_id: str,
    statement: str,
) -> PhotoGeometryAnnotation:
    """Represent the explicit rectified source plane itself as the unit reference."""
    return PhotoGeometryAnnotation(
        id=annotation_id,
        observation_id=observation_id,
        photo_index=rectification.photo_index,
        region=NormalizedImageRegion(x0=0.0, y0=0.0, x1=1.0, y1=1.0),
        source=SourceInfo(kind=SourceKind.INFERRED, confidence=rectification.source.confidence),
        statement=statement,
        coordinate_space_id=rectification.id,
    )
