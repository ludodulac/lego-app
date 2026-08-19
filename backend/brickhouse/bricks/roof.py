"""Deterministic stepped gable-roof generation on the canonical brick grid."""

from __future__ import annotations

from math import floor, hypot
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import RidgeDirection, RoofType
from brickhouse.geometry.models import BuildingGeometry, RoofPlaneGeometry

from .building_layout import BuildingBrickShell


class RoofPartDefinition(BaseModel):
    """Supplier-independent roof part used by the M0 roof generator."""

    id: str
    category: Literal["roof_tile", "ridge_tile"]
    width_studs: int = Field(gt=0)
    length_studs: int = Field(gt=0)
    height_plates: int = Field(default=1, gt=0)


class RoofPartCatalog(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    parts: list[RoofPartDefinition]

    def get(self, part_id: str) -> RoofPartDefinition:
        for part in self.parts:
            if part.id == part_id:
                return part
        raise KeyError(part_id)


def create_m0_roof_catalog() -> RoofPartCatalog:
    return RoofPartCatalog(
        parts=[
            RoofPartDefinition(id="ROOF_TILE_1X1", category="roof_tile", width_studs=1, length_studs=1),
            RoofPartDefinition(id="ROOF_TILE_1X2", category="roof_tile", width_studs=1, length_studs=2),
            RoofPartDefinition(id="ROOF_TILE_1X4", category="roof_tile", width_studs=1, length_studs=4),
            RoofPartDefinition(id="ROOF_TILE_1X6", category="roof_tile", width_studs=1, length_studs=6),
            RoofPartDefinition(id="ROOF_TILE_1X8", category="roof_tile", width_studs=1, length_studs=8),
            RoofPartDefinition(id="RIDGE_TILE_1X1", category="ridge_tile", width_studs=1, length_studs=1),
            RoofPartDefinition(id="RIDGE_TILE_1X2", category="ridge_tile", width_studs=1, length_studs=2),
            RoofPartDefinition(id="RIDGE_TILE_1X4", category="ridge_tile", width_studs=1, length_studs=4),
            RoofPartDefinition(id="RIDGE_TILE_1X6", category="ridge_tile", width_studs=1, length_studs=6),
            RoofPartDefinition(id="RIDGE_TILE_1X8", category="ridge_tile", width_studs=1, length_studs=8),
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
    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    roof_id: str
    ridge_direction: RidgeDirection
    placements: list[GlobalRoofPlacement]


def _round_half_up(value: float) -> int:
    return floor(value + 0.5)


def _span_part_ids(prefix: str) -> tuple[tuple[int, str], ...]:
    return (
        (8, f"{prefix}_1X8"),
        (6, f"{prefix}_1X6"),
        (4, f"{prefix}_1X4"),
        (2, f"{prefix}_1X2"),
        (1, f"{prefix}_1X1"),
    )


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
    planes = [
        plane
        for plane in geometry.roof_planes
        if plane.volume_id == volume_id and plane.roof_type is RoofType.GABLE
    ]
    if len(planes) != 2:
        raise ValueError("BH-011 requires exactly two gable roof planes for the shell volume")
    by_side = {plane.side: plane for plane in planes}
    if set(by_side) != {"negative", "positive"}:
        raise ValueError("gable roof requires negative and positive planes")
    negative = by_side["negative"]
    positive = by_side["positive"]
    if negative.ridge_direction is None or positive.ridge_direction is None:
        raise ValueError("gable roof planes require ridge_direction")
    if negative.ridge_direction is not positive.ridge_direction:
        raise ValueError("gable roof planes must share ridge_direction")
    return negative, positive


def _occupied_cells(placement: GlobalRoofPlacement) -> set[tuple[int, int, int]]:
    part = create_m0_roof_catalog().get(placement.part_id)
    if placement.rotation_quarter_turns % 2:
        fx, fy = part.length_studs, part.width_studs
    else:
        fx, fy = part.width_studs, part.length_studs
    return {
        (placement.x_studs + dx, placement.y_studs + dy, placement.z_plates)
        for dx in range(fx)
        for dy in range(fy)
    }


def generate_spatial_gable_roof(
    geometry: BuildingGeometry,
    shell: BuildingBrickShell,
) -> SpatialRoof:
    """Generate a deterministic one-plate-thick stepped approximation of a gable roof."""
    negative, positive = _gable_planes(geometry, shell.volume_id)
    ridge_direction = negative.ridge_direction
    assert ridge_direction is not None

    run_m, rise_m = _plane_run_and_rise(negative)
    slope_rise_plates_per_stud = (rise_m / run_m) * 2.5
    wall_top_plates = shell.walls[0].grid.height_bricks * 3

    width = next(record.grid.width_studs for record in shell.walls if record.facade.value == "front")
    depth = next(record.grid.width_studs for record in shell.walls if record.facade.value == "right")

    if ridge_direction is RidgeDirection.DEPTH:
        slope_span = width
        line_length = depth
    else:
        slope_span = depth
        line_length = width

    ridge_axis = (slope_span - 1) / 2.0
    placements: list[GlobalRoofPlacement] = []
    occupied: set[tuple[int, int, int]] = set()

    # One stepped roof row for every grid coordinate across the slope.
    for axis in range(slope_span):
        distance_from_eave = min(axis, slope_span - 1 - axis)
        z = wall_top_plates + _round_half_up(distance_from_eave * slope_rise_plates_per_stud)
        side: Literal["negative", "positive"] = "negative" if axis < ridge_axis else "positive"
        for part_id, offset, _span in _tile_line(line_length, "ROOF_TILE"):
            if ridge_direction is RidgeDirection.DEPTH:
                placement = GlobalRoofPlacement(
                    part_id=part_id,
                    side=side,
                    x_studs=axis,
                    y_studs=offset,
                    z_plates=z,
                    rotation_quarter_turns=0,
                )
            else:
                placement = GlobalRoofPlacement(
                    part_id=part_id,
                    side=side,
                    x_studs=offset,
                    y_studs=axis,
                    z_plates=z,
                    rotation_quarter_turns=1,
                )
            cells = _occupied_cells(placement)
            if occupied.intersection(cells):
                raise RuntimeError("duplicate occupied cells inside generated roof")
            occupied.update(cells)
            placements.append(placement)

    # A single ridge line caps the highest central row(s).
    ridge_axis_int = _round_half_up(ridge_axis)
    ridge_z = wall_top_plates + _round_half_up((slope_span - 1) / 2.0 * slope_rise_plates_per_stud) + 1
    for part_id, offset, _span in _tile_line(line_length, "RIDGE_TILE"):
        if ridge_direction is RidgeDirection.DEPTH:
            placement = GlobalRoofPlacement(
                part_id=part_id,
                side="ridge",
                x_studs=ridge_axis_int,
                y_studs=offset,
                z_plates=ridge_z,
                rotation_quarter_turns=0,
            )
        else:
            placement = GlobalRoofPlacement(
                part_id=part_id,
                side="ridge",
                x_studs=offset,
                y_studs=ridge_axis_int,
                z_plates=ridge_z,
                rotation_quarter_turns=1,
            )
        cells = _occupied_cells(placement)
        if occupied.intersection(cells):
            raise RuntimeError("ridge overlaps generated roof")
        occupied.update(cells)
        placements.append(placement)

    return SpatialRoof(
        building_id=shell.building_id,
        roof_id=negative.roof_id,
        ridge_direction=ridge_direction,
        placements=placements,
    )
