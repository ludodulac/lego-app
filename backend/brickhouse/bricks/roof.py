"""Support-aware gable roof using slope families from the processed piece catalog."""
from __future__ import annotations
from math import atan2, degrees, hypot
from typing import Literal
from pydantic import BaseModel, Field
from brickhouse.building.models import RidgeDirection, RoofType
from brickhouse.geometry.models import BuildingGeometry, RoofPlaneGeometry
from .building_layout import BuildingBrickShell

COURSE_RISE_PLATES = 3

class RoofPartDefinition(BaseModel):
    id: str
    category: Literal["roof_tile", "ridge_tile"]
    width_studs: int = Field(gt=0)
    length_studs: int = Field(gt=0)
    height_plates: int = Field(default=1, gt=0)
    connection_overlap_studs: int = Field(default=0, ge=0)
    slope_family: str | None = None

class RoofPartCatalog(BaseModel):
    schema_version: Literal["0.5"] = "0.5"
    parts: list[RoofPartDefinition]
    def get(self, part_id: str) -> RoofPartDefinition:
        for part in self.parts:
            if part.id == part_id:
                return part
        raise KeyError(part_id)

class RoofSlopeFamily(BaseModel):
    id: str
    pitch_degrees: float
    footprint_depth_studs: int = Field(gt=0)
    course_advance_studs: int = Field(gt=0)
    rise_plates: int = Field(gt=0)
    line_parts: tuple[tuple[int, str], ...]

SUPPORTED_SLOPE_FAMILIES: tuple[RoofSlopeFamily, ...] = (
    RoofSlopeFamily(
        id="33",
        pitch_degrees=33.0,
        footprint_depth_studs=3,
        course_advance_studs=2,
        rise_plates=3,
        line_parts=((6, "BRICK_SLOPED_33_3X6"), (4, "BRICK_SLOPED_33_3X4"), (2, "BRICK_SLOPED_33_3X2")),
    ),
    RoofSlopeFamily(
        id="45",
        pitch_degrees=45.0,
        footprint_depth_studs=2,
        course_advance_studs=1,
        rise_plates=3,
        line_parts=((4, "BRICK_SLOPED_45_2X4"), (3, "BRICK_SLOPED_45_2X3"), (2, "BRICK_SLOPED_45_2X2"), (1, "BRICK_SLOPED_45_2X1")),
    ),
)

def select_roof_slope_family(target_pitch_degrees: float) -> RoofSlopeFamily:
    """Return the closest structurally modeled slope family; lower pitch wins exact ties."""
    if target_pitch_degrees <= 0:
        raise ValueError("roof pitch must be positive")
    return min(SUPPORTED_SLOPE_FAMILIES, key=lambda family: (abs(family.pitch_degrees - target_pitch_degrees), family.pitch_degrees))

def create_m0_roof_catalog() -> RoofPartCatalog:
    parts: list[RoofPartDefinition] = []
    for family in SUPPORTED_SLOPE_FAMILIES:
        for span, part_id in family.line_parts:
            parts.append(RoofPartDefinition(
                id=part_id,
                category="roof_tile",
                width_studs=family.footprint_depth_studs,
                length_studs=span,
                height_plates=family.rise_plates,
                connection_overlap_studs=family.footprint_depth_studs-family.course_advance_studs,
                slope_family=family.id,
            ))
    parts.extend([
        RoofPartDefinition(id="TILE_2X2", category="ridge_tile", width_studs=2, length_studs=2, height_plates=1, connection_overlap_studs=1),
        RoofPartDefinition(id="TILE_2X3", category="ridge_tile", width_studs=2, length_studs=3, height_plates=1, connection_overlap_studs=1),
        RoofPartDefinition(id="TILE_2X4", category="ridge_tile", width_studs=2, length_studs=4, height_plates=1, connection_overlap_studs=1),
    ])
    return RoofPartCatalog(parts=parts)

class GlobalRoofPlacement(BaseModel):
    part_id: str
    side: Literal["negative", "positive", "ridge"]
    x_studs: int
    y_studs: int
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3]

class SpatialRoof(BaseModel):
    schema_version: Literal["0.5"] = "0.5"
    building_id: str
    roof_id: str
    ridge_direction: RidgeDirection
    placements: list[GlobalRoofPlacement]

def _tile_line(length: int, kind: str, family: RoofSlopeFamily | None = None) -> list[tuple[str, int, int]]:
    if kind == "slope":
        if family is None:
            raise ValueError("slope tiling requires a slope family")
        choices = family.line_parts
    else:
        choices = ((4, "TILE_2X4"), (3, "TILE_2X3"), (2, "TILE_2X2"))
    out: list[tuple[str, int, int]] = []
    cursor = 0
    for span, part_id in choices:
        while cursor + span <= length:
            out.append((part_id, cursor, span))
            cursor += span
    if cursor != length:
        family_label = family.id if family else "ridge"
        raise ValueError(f"roof family {family_label} cannot tile line length {length} with available catalog parts")
    return out

def _plane_run_and_rise(plane: RoofPlaneGeometry) -> tuple[float, float]:
    low = min(point.z for point in plane.corners)
    high = max(point.z for point in plane.corners)
    eave = [point for point in plane.corners if abs(point.z-low) < 1e-9]
    ridge = [point for point in plane.corners if abs(point.z-high) < 1e-9]
    if high <= low or not eave or not ridge:
        raise ValueError("invalid gable roof plane")
    run = hypot(eave[0].x-ridge[0].x, eave[0].y-ridge[0].y)
    if run <= 0:
        raise ValueError("gable roof plane must have positive horizontal run")
    return run, high-low

def _gable_planes(geometry: BuildingGeometry, volume_id: str) -> tuple[RoofPlaneGeometry, RoofPlaneGeometry]:
    planes = [plane for plane in geometry.roof_planes if plane.volume_id == volume_id and plane.roof_type is RoofType.GABLE]
    if len(planes) != 2:
        raise ValueError("BH-028 requires exactly two gable roof planes for the shell volume")
    by_side = {plane.side: plane for plane in planes}
    negative, positive = by_side.get("negative"), by_side.get("positive")
    if negative is None or positive is None:
        raise ValueError("gable roof requires negative and positive planes")
    if negative.ridge_direction is None or positive.ridge_direction is None or negative.ridge_direction is not positive.ridge_direction:
        raise ValueError("gable roof planes must share ridge_direction")
    return negative, positive

def _footprint(placement: GlobalRoofPlacement) -> set[tuple[int, int]]:
    definition = create_m0_roof_catalog().get(placement.part_id)
    footprint_x, footprint_y = ((definition.length_studs, definition.width_studs) if placement.rotation_quarter_turns % 2 else (definition.width_studs, definition.length_studs))
    return {(placement.x_studs+dx, placement.y_studs+dy) for dx in range(footprint_x) for dy in range(footprint_y)}

def _axis(placement: GlobalRoofPlacement, direction: RidgeDirection) -> int:
    return placement.x_studs if direction is RidgeDirection.DEPTH else placement.y_studs

def _family_for_placements(placements: list[GlobalRoofPlacement]) -> RoofSlopeFamily:
    catalog = create_m0_roof_catalog()
    family_ids = {catalog.get(placement.part_id).slope_family for placement in placements}
    family_ids.discard(None)
    if len(family_ids) != 1:
        raise ValueError("roof side must use exactly one slope family")
    family_id = next(iter(family_ids))
    return next(family for family in SUPPORTED_SLOPE_FAMILIES if family.id == family_id)

def validate_roof_support(roof: SpatialRoof, shell: BuildingBrickShell) -> None:
    top = shell.walls[0].grid.height_bricks * 3
    width = next(record.grid.width_studs for record in shell.walls if record.facade.value == "front")
    depth = next(record.grid.width_studs for record in shell.walls if record.facade.value == "right")
    side_families: dict[str, RoofSlopeFamily] = {}
    for side in ("negative", "positive"):
        placements = [placement for placement in roof.placements if placement.side == side]
        if not placements:
            raise ValueError(f"roof side {side!r} has no slope courses")
        family = _family_for_placements(placements)
        side_families[side] = family
        axes = sorted({_axis(placement, roof.ridge_direction) for placement in placements}, reverse=side == "positive")
        courses = [[placement for placement in placements if _axis(placement, roof.ridge_direction) == axis] for axis in axes]
        if any(placement.z_plates != top for placement in courses[0]):
            raise ValueError(f"roof side {side!r} eave course is not anchored at wall top")
        first_footprint = set().union(*(_footprint(placement) for placement in courses[0]))
        edge = 0 if side == "negative" else (width-1 if roof.ridge_direction is RidgeDirection.DEPTH else depth-1)
        if not any((x == edge if roof.ridge_direction is RidgeDirection.DEPTH else y == edge) for x, y in first_footprint):
            raise ValueError(f"roof side {side!r} does not contact its eave wall")
        for previous_axis, current_axis, previous, current in zip(axes, axes[1:], courses, courses[1:]):
            if abs(current_axis-previous_axis) != family.course_advance_studs:
                raise ValueError(f"roof side {side!r} does not follow selected slope course advance")
            if not set().union(*(_footprint(placement) for placement in previous)).intersection(set().union(*(_footprint(placement) for placement in current))):
                raise ValueError(f"floating roof course on side {side!r}")
            if min(placement.z_plates for placement in current)-min(placement.z_plates for placement in previous) != family.rise_plates:
                raise ValueError(f"roof side {side!r} does not follow the selected slope connection rise")
    if side_families["negative"].id != side_families["positive"].id:
        raise ValueError("both roof sides must use the same slope family")
    ridge = [placement for placement in roof.placements if placement.side == "ridge"]
    if not ridge:
        raise ValueError("roof has no ridge")
    ridge_cells = set().union(*(_footprint(placement) for placement in ridge))
    for side in ("negative", "positive"):
        placements = [placement for placement in roof.placements if placement.side == side]
        axes = sorted({_axis(placement, roof.ridge_direction) for placement in placements}, reverse=side == "positive")
        inner_axis = axes[-1]
        inner_cells = set().union(*(_footprint(placement) for placement in placements if _axis(placement, roof.ridge_direction) == inner_axis))
        if not ridge_cells.intersection(inner_cells):
            raise ValueError(f"ridge is not connected to roof side {side!r}")

def _course_count(span: int, family: RoofSlopeFamily) -> int:
    count = 0
    while True:
        candidate = count + 1
        negative_axis = (candidate-1) * family.course_advance_studs
        positive_axis = span-family.footprint_depth_studs-(candidate-1)*family.course_advance_studs
        if negative_axis >= positive_axis:
            break
        count = candidate
    return count

def generate_spatial_gable_roof(geometry: BuildingGeometry, shell: BuildingBrickShell) -> SpatialRoof:
    negative, _ = _gable_planes(geometry, shell.volume_id)
    run, rise = _plane_run_and_rise(negative)
    target_pitch = degrees(atan2(rise, run))
    family = select_roof_slope_family(target_pitch)
    direction = negative.ridge_direction
    assert direction is not None
    top = shell.walls[0].grid.height_bricks * 3
    width = next(record.grid.width_studs for record in shell.walls if record.facade.value == "front")
    depth = next(record.grid.width_studs for record in shell.walls if record.facade.value == "right")
    span, line_length = (width, depth) if direction is RidgeDirection.DEPTH else (depth, width)

    # A two-stud ridge cannot be centered on an odd shell span while touching
    # both symmetric slope families. Instead of rejecting an otherwise valid
    # building (or distorting the wall grid), extend the roof footprint by one
    # stud on the positive eave. The first positive slope course still overlaps
    # the actual wall edge, so support validation remains meaningful; the extra
    # stud is simply a small roof overhang at LEGO-grid resolution.
    roof_span = span if span % 2 == 0 else span + 1

    course_count = _course_count(roof_span, family)
    if course_count < 1:
        raise ValueError("roof span is too small for selected supported slope family and ridge")
    placements: list[GlobalRoofPlacement] = []
    for side in ("negative", "positive"):
        for distance in range(course_count):
            axis = distance*family.course_advance_studs if side == "negative" else roof_span-family.footprint_depth_studs-distance*family.course_advance_studs
            z_plates = top + distance*family.rise_plates
            for part_id, offset, _ in _tile_line(line_length, "slope", family):
                placements.append(GlobalRoofPlacement(
                    part_id=part_id,
                    side=side,
                    x_studs=axis if direction is RidgeDirection.DEPTH else offset,
                    y_studs=offset if direction is RidgeDirection.DEPTH else axis,
                    z_plates=z_plates,
                    rotation_quarter_turns=0 if direction is RidgeDirection.DEPTH else 1,
                ))
    ridge_axis = roof_span//2 - 1
    ridge_z = top + course_count*family.rise_plates
    for part_id, offset, _ in _tile_line(line_length, "ridge"):
        placements.append(GlobalRoofPlacement(
            part_id=part_id,
            side="ridge",
            x_studs=ridge_axis if direction is RidgeDirection.DEPTH else offset,
            y_studs=offset if direction is RidgeDirection.DEPTH else ridge_axis,
            z_plates=ridge_z,
            rotation_quarter_turns=0 if direction is RidgeDirection.DEPTH else 1,
        ))
    roof = SpatialRoof(building_id=shell.building_id, roof_id=negative.roof_id, ridge_direction=direction, placements=placements)
    validate_roof_support(roof, shell)
    return roof
