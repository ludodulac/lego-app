"""Deterministic, support-aware gable-roof generation on the canonical brick grid."""

from __future__ import annotations

from math import floor, hypot
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import RidgeDirection, RoofType
from brickhouse.geometry.models import BuildingGeometry, RoofPlaneGeometry

from .building_layout import BuildingBrickShell


class RoofPartDefinition(BaseModel):
    """Supplier-independent roof part with explicit connection semantics."""

    id: str
    category: Literal["roof_tile", "ridge_tile"]
    width_studs: int = Field(gt=0)
    length_studs: int = Field(gt=0)
    height_plates: int = Field(default=1, gt=0)
    connection_overlap_studs: int = Field(default=0, ge=0)


class RoofPartCatalog(BaseModel):
    schema_version: Literal["0.2"] = "0.2"
    parts: list[RoofPartDefinition]

    def get(self, part_id: str) -> RoofPartDefinition:
        for part in self.parts:
            if part.id == part_id:
                return part
        raise KeyError(part_id)


def create_m0_roof_catalog() -> RoofPartCatalog:
    """Return the first support-aware canonical roof family.

    A slope is two studs deep across the roof pitch. Consecutive courses advance
    by one stud, so one stud row overlaps in plan with the previous course. The
    overlap represents the stud/underside connection that carries the new course.
    """
    spans = (1, 2, 4, 6, 8)
    return RoofPartCatalog(
        parts=[
            *[
                RoofPartDefinition(
                    id=f"ROOF_SLOPE_2X{span}",
                    category="roof_tile",
                    width_studs=2,
                    length_studs=span,
                    connection_overlap_studs=1,
                )
                for span in spans
            ],
            *[
                RoofPartDefinition(
                    id=f"RIDGE_TILE_1X{span}",
                    category="ridge_tile",
                    width_studs=1,
                    length_studs=span,
                    connection_overlap_studs=1,
                )
                for span in spans
            ],
        ]
    )


class GlobalRoofPlacement(BaseModel):
    part_id: str
    side: Literal["negative", "positive", "ridge"]
    x_studs: int
    y_studs: int
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3]


class SpatialRoof(BaseModel):
    schema_version: Literal["0.2"] = "0.2"
    building_id: str
    roof_id: str
    ridge_direction: RidgeDirection
    placements: list[GlobalRoofPlacement]


def _round_half_up(value: float) -> int:
    return floor(value + 0.5)


def _span_part_ids(prefix: str) -> tuple[tuple[int, str], ...]:
    if prefix == "ROOF_SLOPE":
        return tuple((span, f"ROOF_SLOPE_2X{span}") for span in (8, 6, 4, 2, 1))
    return tuple((span, f"RIDGE_TILE_1X{span}") for span in (8, 6, 4, 2, 1))


def _tile_line(length: int, prefix: str) -> list[tuple[str, int, int]]:
    result: list[tuple[str, int, int]] = []
    cursor = 0
    for span, part_id in _span_part_ids(prefix):
        while cursor + span <= length:
            result.append((part_id, cursor, span))
            cursor += span
    if cursor != length:
        raise RuntimeError(f"could not tile roof line of length {length}")
    return result


def _plane_run_and_rise(plane: RoofPlaneGeometry) -> tuple[float, float]:
    eave_z = min(point.z for point in plane.corners)
    ridge_z = max(point.z for point in plane.corners)
    rise = ridge_z - eave_z
    if rise <= 0:
        raise ValueError("gable roof plane must have positive rise")
    eave_points = [point for point in plane.corners if abs(point.z - eave_z) < 1e-9]
    ridge_points = [point for point in plane.corners if abs(point.z - ridge_z) < 1e-9]
    if not eave_points or not ridge_points:
        raise ValueError("could not identify roof eave and ridge")
    a, b = eave_points[0], ridge_points[0]
    run = hypot(a.x - b.x, a.y - b.y)
    if run <= 0:
        raise ValueError("gable roof plane must have positive horizontal run")
    return run, rise


def _gable_planes(geometry: BuildingGeometry, volume_id: str) -> tuple[RoofPlaneGeometry, RoofPlaneGeometry]:
    planes = [p for p in geometry.roof_planes if p.volume_id == volume_id and p.roof_type is RoofType.GABLE]
    if len(planes) != 2:
        raise ValueError("BH-025 requires exactly two gable roof planes for the shell volume")
    by_side = {plane.side: plane for plane in planes}
    if set(by_side) != {"negative", "positive"}:
        raise ValueError("gable roof requires negative and positive planes")
    negative, positive = by_side["negative"], by_side["positive"]
    if negative.ridge_direction is None or positive.ridge_direction is None:
        raise ValueError("gable roof planes require ridge_direction")
    if negative.ridge_direction is not positive.ridge_direction:
        raise ValueError("gable roof planes must share ridge_direction")
    return negative, positive


def _footprint(placement: GlobalRoofPlacement) -> set[tuple[int, int]]:
    part = create_m0_roof_catalog().get(placement.part_id)
    fx, fy = (part.length_studs, part.width_studs) if placement.rotation_quarter_turns % 2 else (part.width_studs, part.length_studs)
    return {(placement.x_studs + dx, placement.y_studs + dy) for dx in range(fx) for dy in range(fy)}


def _course_axis(placement: GlobalRoofPlacement, ridge_direction: RidgeDirection) -> int:
    return placement.x_studs if ridge_direction is RidgeDirection.DEPTH else placement.y_studs


def validate_roof_support(roof: SpatialRoof, shell: BuildingBrickShell) -> None:
    """Reject floating roof courses.

    M0 rule: the eave course is anchored on the wall perimeter. Every later
    slope course must overlap the preceding course by at least one stud row in
    plan and may rise by at most six plates per one-stud advance. Ridge parts
    must overlap the innermost course of at least one roof side.
    """
    catalog = create_m0_roof_catalog()
    wall_top = shell.walls[0].grid.height_bricks * 3
    width = next(r.grid.width_studs for r in shell.walls if r.facade.value == "front")
    depth = next(r.grid.width_studs for r in shell.walls if r.facade.value == "right")

    for side in ("negative", "positive"):
        side_parts = [p for p in roof.placements if p.side == side]
        axes = sorted({_course_axis(p, roof.ridge_direction) for p in side_parts}, reverse=side == "positive")
        if not axes:
            raise ValueError(f"roof side {side!r} has no slope courses")
        courses = [[p for p in side_parts if _course_axis(p, roof.ridge_direction) == axis] for axis in axes]
        first = courses[0]
        if any(p.z_plates != wall_top for p in first):
            raise ValueError(f"roof side {side!r} eave course is not anchored at wall top")
        # Eave footprints must touch the exterior perimeter.
        first_cells = set().union(*(_footprint(p) for p in first))
        if roof.ridge_direction is RidgeDirection.DEPTH:
            expected_edge = 0 if side == "negative" else width - 1
            if not any(x == expected_edge for x, _ in first_cells):
                raise ValueError(f"roof side {side!r} does not contact its eave wall")
        else:
            expected_edge = 0 if side == "negative" else depth - 1
            if not any(y == expected_edge for _, y in first_cells):
                raise ValueError(f"roof side {side!r} does not contact its eave wall")

        for previous, current in zip(courses, courses[1:]):
            prev_cells = set().union(*(_footprint(p) for p in previous))
            current_cells = set().union(*(_footprint(p) for p in current))
            if not prev_cells.intersection(current_cells):
                raise ValueError(f"floating roof course on side {side!r}")
            prev_z = min(p.z_plates for p in previous)
            current_z = min(p.z_plates for p in current)
            if current_z < prev_z or current_z - prev_z > 6:
                raise ValueError(f"unsupported vertical jump on roof side {side!r}")
            for p in current:
                if catalog.get(p.part_id).connection_overlap_studs < 1:
                    raise ValueError(f"roof part {p.part_id!r} has no connection overlap")

    ridge_parts = [p for p in roof.placements if p.side == "ridge"]
    if not ridge_parts:
        raise ValueError("roof has no ridge")
    ridge_cells = set().union(*(_footprint(p) for p in ridge_parts))
    inner_cells: set[tuple[int, int]] = set()
    for side in ("negative", "positive"):
        side_parts = [p for p in roof.placements if p.side == side]
        axes = sorted({_course_axis(p, roof.ridge_direction) for p in side_parts}, reverse=side == "positive")
        inner_axis = axes[-1]
        inner_cells.update(*(_footprint(p) for p in side_parts if _course_axis(p, roof.ridge_direction) == inner_axis))
    if not ridge_cells.intersection(inner_cells):
        raise ValueError("ridge is not connected to the innermost roof courses")


def generate_spatial_gable_roof(geometry: BuildingGeometry, shell: BuildingBrickShell) -> SpatialRoof:
    """Generate an overlap-supported stepped gable roof."""
    negative, positive = _gable_planes(geometry, shell.volume_id)
    ridge_direction = negative.ridge_direction
    assert ridge_direction is not None
    run_m, rise_m = _plane_run_and_rise(negative)
    rise_per_stud = (rise_m / run_m) * 2.5
    wall_top = shell.walls[0].grid.height_bricks * 3
    width = next(r.grid.width_studs for r in shell.walls if r.facade.value == "front")
    depth = next(r.grid.width_studs for r in shell.walls if r.facade.value == "right")
    slope_span, line_length = (width, depth) if ridge_direction is RidgeDirection.DEPTH else (depth, width)
    half = slope_span // 2
    placements: list[GlobalRoofPlacement] = []

    # Two-stud-deep courses advance inward one stud at a time. Their footprints
    # overlap one row, forming an explicit support/connection chain.
    for side in ("negative", "positive"):
        for distance in range(half):
            axis = distance if side == "negative" else slope_span - 2 - distance
            if axis < 0:
                continue
            z = wall_top + _round_half_up(distance * rise_per_stud)
            for part_id, offset, _span in _tile_line(line_length, "ROOF_SLOPE"):
                if ridge_direction is RidgeDirection.DEPTH:
                    placement = GlobalRoofPlacement(part_id=part_id, side=side, x_studs=axis, y_studs=offset, z_plates=z, rotation_quarter_turns=0)
                else:
                    placement = GlobalRoofPlacement(part_id=part_id, side=side, x_studs=offset, y_studs=axis, z_plates=z, rotation_quarter_turns=1)
                placements.append(placement)

    ridge_axis = max(0, (slope_span - 1) // 2)
    ridge_z = wall_top + _round_half_up(max(0, half - 1) * rise_per_stud) + 1
    for part_id, offset, _span in _tile_line(line_length, "RIDGE_TILE"):
        if ridge_direction is RidgeDirection.DEPTH:
            placements.append(GlobalRoofPlacement(part_id=part_id, side="ridge", x_studs=ridge_axis, y_studs=offset, z_plates=ridge_z, rotation_quarter_turns=0))
        else:
            placements.append(GlobalRoofPlacement(part_id=part_id, side="ridge", x_studs=offset, y_studs=ridge_axis, z_plates=ridge_z, rotation_quarter_turns=1))

    roof = SpatialRoof(building_id=shell.building_id, roof_id=negative.roof_id, ridge_direction=ridge_direction, placements=placements)
    validate_roof_support(roof, shell)
    return roof
