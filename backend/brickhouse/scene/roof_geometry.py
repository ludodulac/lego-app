"""Internal exact roof geometry derived from ArchitecturalScene truth.

The public ArchitecturalScene remains the metric source of truth. This module
only derives construction-independent geometric queries when the Scene already
contains enough exact information. It never chooses a pitch from a range or
invents a ridge direction.
"""
from __future__ import annotations

from math import radians, tan
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building import RidgeDirection

from .models import EPSILON, SceneRoof, SceneRoofType, SceneVolume


RoofGeometryStatus = Literal[
    "exact_gable",
    "unsupported_roof_type",
    "unknown_host_geometry",
    "missing_exact_pitch",
    "missing_ridge_direction",
]
RoofSlopeAxis = Literal["x", "y"]
RoofPlaneSide = Literal["negative", "positive"]


class RoofLine(BaseModel):
    """Axis-aligned horizontal line segment in the canonical Scene frame."""

    axis: RoofSlopeAxis
    fixed_coordinate: float
    span_min: float
    span_max: float
    z: float


class GableRoofPlane(BaseModel):
    """One planar half of an exact symmetric gable roof."""

    plane_id: str
    side: RoofPlaneSide
    slope_axis: RoofSlopeAxis
    ridge_coordinate: float
    slope_min: float
    slope_max: float
    span_min: float
    span_max: float
    ridge_z: float
    pitch_degrees: float

    def contains_xy(self, x: float, y: float, *, tolerance: float = EPSILON) -> bool:
        slope_coordinate = x if self.slope_axis == "x" else y
        span_coordinate = y if self.slope_axis == "x" else x
        return (
            self.slope_min - tolerance <= slope_coordinate <= self.slope_max + tolerance
            and self.span_min - tolerance <= span_coordinate <= self.span_max + tolerance
        )

    def z_at(self, x: float, y: float) -> float | None:
        if not self.contains_xy(x, y):
            return None
        slope_coordinate = x if self.slope_axis == "x" else y
        return self.ridge_z - abs(slope_coordinate - self.ridge_coordinate) * tan(
            radians(self.pitch_degrees)
        )


class GableRoofGeometry(BaseModel):
    roof_id: str
    volume_id: str
    ridge_direction: RidgeDirection
    slope_axis: RoofSlopeAxis
    wall_top_z: float
    ridge_z: float
    overhang: float = Field(ge=0)
    ridge: RoofLine
    support_lines: list[RoofLine]
    eaves: list[RoofLine]
    planes: list[GableRoofPlane]

    def z_at(self, x: float, y: float) -> float | None:
        values = [plane.z_at(x, y) for plane in self.planes]
        known = [value for value in values if value is not None]
        if not known:
            return None
        # On the ridge both planes intentionally return the same value.
        return max(known)


class RoofGeometryAssessment(BaseModel):
    roof_id: str
    volume_id: str
    status: RoofGeometryStatus
    geometry: GableRoofGeometry | None = None


def _complete_volume_metrics(volume: SceneVolume) -> tuple[float, float, float] | None:
    width = volume.width.value
    depth = volume.depth.value
    height = volume.height.value
    if width is None or depth is None or height is None:
        return None
    return width, depth, height


def derive_roof_geometry(roof: SceneRoof, volume: SceneVolume) -> RoofGeometryAssessment:
    """Derive exact gable planes when the Scene provides all required metrics."""
    if roof.type is not SceneRoofType.GABLE:
        return RoofGeometryAssessment(
            roof_id=roof.id,
            volume_id=roof.volume_id,
            status="unsupported_roof_type",
        )
    metrics = _complete_volume_metrics(volume)
    if metrics is None:
        return RoofGeometryAssessment(
            roof_id=roof.id,
            volume_id=roof.volume_id,
            status="unknown_host_geometry",
        )
    if roof.pitch_degrees is None:
        return RoofGeometryAssessment(
            roof_id=roof.id,
            volume_id=roof.volume_id,
            status="missing_exact_pitch",
        )
    if roof.ridge_direction is None:
        return RoofGeometryAssessment(
            roof_id=roof.id,
            volume_id=roof.volume_id,
            status="missing_ridge_direction",
        )

    width, depth, height = metrics
    wall_top_z = volume.position.z + height
    pitch_tangent = tan(radians(roof.pitch_degrees))

    if roof.ridge_direction is RidgeDirection.DEPTH:
        slope_axis: RoofSlopeAxis = "x"
        host_slope_min = volume.position.x
        host_slope_max = volume.position.x + width
        host_span_min = volume.position.y
        host_span_max = volume.position.y + depth
    else:
        slope_axis = "y"
        host_slope_min = volume.position.y
        host_slope_max = volume.position.y + depth
        host_span_min = volume.position.x
        host_span_max = volume.position.x + width

    ridge_coordinate = (host_slope_min + host_slope_max) / 2.0
    half_host_span = (host_slope_max - host_slope_min) / 2.0
    ridge_z = wall_top_z + half_host_span * pitch_tangent
    outer_min = host_slope_min - roof.overhang
    outer_max = host_slope_max + roof.overhang
    outer_span_min = host_span_min - roof.overhang
    outer_span_max = host_span_max + roof.overhang
    outer_eave_z = wall_top_z - roof.overhang * pitch_tangent

    ridge = RoofLine(
        axis=slope_axis,
        fixed_coordinate=ridge_coordinate,
        span_min=outer_span_min,
        span_max=outer_span_max,
        z=ridge_z,
    )
    support_lines = [
        RoofLine(
            axis=slope_axis,
            fixed_coordinate=host_slope_min,
            span_min=host_span_min,
            span_max=host_span_max,
            z=wall_top_z,
        ),
        RoofLine(
            axis=slope_axis,
            fixed_coordinate=host_slope_max,
            span_min=host_span_min,
            span_max=host_span_max,
            z=wall_top_z,
        ),
    ]
    eaves = [
        RoofLine(
            axis=slope_axis,
            fixed_coordinate=outer_min,
            span_min=outer_span_min,
            span_max=outer_span_max,
            z=outer_eave_z,
        ),
        RoofLine(
            axis=slope_axis,
            fixed_coordinate=outer_max,
            span_min=outer_span_min,
            span_max=outer_span_max,
            z=outer_eave_z,
        ),
    ]
    planes = [
        GableRoofPlane(
            plane_id=f"{roof.id}:negative",
            side="negative",
            slope_axis=slope_axis,
            ridge_coordinate=ridge_coordinate,
            slope_min=outer_min,
            slope_max=ridge_coordinate,
            span_min=outer_span_min,
            span_max=outer_span_max,
            ridge_z=ridge_z,
            pitch_degrees=roof.pitch_degrees,
        ),
        GableRoofPlane(
            plane_id=f"{roof.id}:positive",
            side="positive",
            slope_axis=slope_axis,
            ridge_coordinate=ridge_coordinate,
            slope_min=ridge_coordinate,
            slope_max=outer_max,
            span_min=outer_span_min,
            span_max=outer_span_max,
            ridge_z=ridge_z,
            pitch_degrees=roof.pitch_degrees,
        ),
    ]
    return RoofGeometryAssessment(
        roof_id=roof.id,
        volume_id=roof.volume_id,
        status="exact_gable",
        geometry=GableRoofGeometry(
            roof_id=roof.id,
            volume_id=roof.volume_id,
            ridge_direction=roof.ridge_direction,
            slope_axis=slope_axis,
            wall_top_z=wall_top_z,
            ridge_z=ridge_z,
            overhang=roof.overhang,
            ridge=ridge,
            support_lines=support_lines,
            eaves=eaves,
            planes=planes,
        ),
    )


def derive_scene_roof_geometry(scene) -> tuple[RoofGeometryAssessment, ...]:
    """Return deterministic roof assessments without mutating the Scene."""
    volumes = {volume.id: volume for volume in scene.volumes}
    assessments = [derive_roof_geometry(roof, volumes[roof.volume_id]) for roof in scene.roofs]
    return tuple(sorted(assessments, key=lambda item: item.roof_id))
