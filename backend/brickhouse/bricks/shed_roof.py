"""Support-aware mono-pitch roof placement using validated slope families."""
from __future__ import annotations

from math import atan2, degrees, hypot
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import Facade, RoofType
from brickhouse.geometry.models import BuildingGeometry, RoofPlaneGeometry
from .building_layout import BuildingBrickShell
from .roof import RoofSlopeFamily, create_m0_roof_catalog, select_roof_slope_family


class ShedRoofPlacement(BaseModel):
    part_id: str
    side: Literal["slope"] = "slope"
    x_studs: int = Field(ge=0)
    y_studs: int = Field(ge=0)
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3]


class SpatialShedRoof(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    roof_id: str
    roof_type: Literal[RoofType.SHED] = RoofType.SHED
    down_slope_direction: Facade
    placements: list[ShedRoofPlacement] = Field(min_length=1)


def _shed_plane(geometry: BuildingGeometry, volume_id: str) -> RoofPlaneGeometry:
    planes = [
        plane for plane in geometry.roof_planes
        if plane.volume_id == volume_id and plane.roof_type is RoofType.SHED
    ]
    if len(planes) != 1:
        raise ValueError("shed roof requires exactly one roof plane for the shell volume")
    plane = planes[0]
    if plane.down_slope_direction is None:
        raise ValueError("shed roof plane requires down_slope_direction")
    return plane


def _run_and_rise(plane: RoofPlaneGeometry) -> tuple[float, float]:
    low = min(point.z for point in plane.corners)
    high = max(point.z for point in plane.corners)
    low_points = [point for point in plane.corners if abs(point.z - low) < 1e-9]
    high_points = [point for point in plane.corners if abs(point.z - high) < 1e-9]
    run = min(
        hypot(low_point.x - high_point.x, low_point.y - high_point.y)
        for low_point in low_points for high_point in high_points
    )
    if run <= 0 or high <= low:
        raise ValueError("shed roof plane must have positive run and rise")
    return run, high - low


def _tile_line(length: int, family: RoofSlopeFamily) -> list[tuple[str, int]]:
    choices = family.line_parts
    cursor = 0
    out: list[tuple[str, int]] = []
    while cursor < length:
        for span, part_id in choices:
            if cursor + span <= length:
                out.append((part_id, cursor))
                cursor += span
                break
        else:
            raise ValueError(
                f"roof family {family.id} cannot tile line length {length} with available catalog parts"
            )
    return out


def _connected_span(wall_span: int, family: RoofSlopeFamily) -> int:
    """Quantize only LEGO coverage, never architectural pitch or direction."""
    span = wall_span
    while (span - family.footprint_depth_studs) % family.course_advance_studs:
        span += 1
    return span


def _placement_footprint(placement: ShedRoofPlacement) -> set[tuple[int, int]]:
    definition = create_m0_roof_catalog().get(placement.part_id)
    sx, sy = (
        (definition.length_studs, definition.width_studs)
        if placement.rotation_quarter_turns % 2
        else (definition.width_studs, definition.length_studs)
    )
    return {
        (placement.x_studs + dx, placement.y_studs + dy)
        for dx in range(sx) for dy in range(sy)
    }


def validate_shed_roof_support(roof: SpatialShedRoof, shell: BuildingBrickShell) -> None:
    family_ids = {
        create_m0_roof_catalog().get(placement.part_id).slope_family
        for placement in roof.placements
    }
    if len(family_ids) != 1 or None in family_ids:
        raise ValueError("shed roof must use exactly one validated slope family")
    family_id = next(iter(family_ids))
    family = next(item for item in (select_roof_slope_family(18), select_roof_slope_family(33), select_roof_slope_family(45)) if item.id == family_id)
    top = shell.walls[0].grid.height_bricks * 3
    width = next(record.grid.width_studs for record in shell.walls if record.facade.value == "front")
    depth = next(record.grid.width_studs for record in shell.walls if record.facade.value == "right")
    direction = roof.down_slope_direction
    axis_is_y = direction in {Facade.FRONT, Facade.REAR}
    axis_values = sorted({p.y_studs if axis_is_y else p.x_studs for p in roof.placements})
    low_to_high = axis_values if direction in {Facade.FRONT, Facade.LEFT} else list(reversed(axis_values))
    courses = [[p for p in roof.placements if (p.y_studs if axis_is_y else p.x_studs) == axis] for axis in low_to_high]
    if min(p.z_plates for p in courses[0]) != top:
        raise ValueError("shed low eave course is not anchored at wall top")
    for previous, current in zip(courses, courses[1:]):
        if min(p.z_plates for p in current) - min(p.z_plates for p in previous) != family.rise_plates:
            raise ValueError("shed roof courses do not follow selected slope rise")
        if not set().union(*(_placement_footprint(p) for p in previous)).intersection(
            set().union(*(_placement_footprint(p) for p in current))
        ):
            raise ValueError("floating shed roof course")
    all_cells = set().union(*(_placement_footprint(p) for p in roof.placements))
    low_edge = {
        Facade.FRONT: lambda x, y: y == 0,
        Facade.REAR: lambda x, y: y == depth - 1,
        Facade.LEFT: lambda x, y: x == 0,
        Facade.RIGHT: lambda x, y: x == width - 1,
    }[direction]
    high_edge = {
        Facade.FRONT: lambda x, y: y == depth - 1,
        Facade.REAR: lambda x, y: y == 0,
        Facade.LEFT: lambda x, y: x == width - 1,
        Facade.RIGHT: lambda x, y: x == 0,
    }[direction]
    if not any(low_edge(x, y) for x, y in all_cells):
        raise ValueError("shed roof does not contact the low wall")
    if not any(high_edge(x, y) for x, y in all_cells):
        raise ValueError("shed roof does not reach the high wall")


def generate_spatial_shed_roof(geometry: BuildingGeometry, shell: BuildingBrickShell) -> SpatialShedRoof:
    plane = _shed_plane(geometry, shell.volume_id)
    run, rise = _run_and_rise(plane)
    family = select_roof_slope_family(degrees(atan2(rise, run)))
    direction = plane.down_slope_direction
    assert direction is not None
    top = shell.walls[0].grid.height_bricks * 3
    width = next(record.grid.width_studs for record in shell.walls if record.facade.value == "front")
    depth = next(record.grid.width_studs for record in shell.walls if record.facade.value == "right")
    axis_is_y = direction in {Facade.FRONT, Facade.REAR}
    wall_span = depth if axis_is_y else width
    line_length = width if axis_is_y else depth
    roof_span = _connected_span(wall_span, family)
    count = (roof_span - family.footprint_depth_studs) // family.course_advance_studs + 1
    placements: list[ShedRoofPlacement] = []
    low_positive = direction in {Facade.REAR, Facade.RIGHT}
    for distance in range(count):
        axis = (
            roof_span - family.footprint_depth_studs - distance * family.course_advance_studs
            if low_positive else distance * family.course_advance_studs
        )
        z = top + distance * family.rise_plates
        for part_id, offset in _tile_line(line_length, family):
            placements.append(ShedRoofPlacement(
                part_id=part_id,
                x_studs=offset if axis_is_y else axis,
                y_studs=axis if axis_is_y else offset,
                z_plates=z,
                rotation_quarter_turns=1 if axis_is_y else 0,
            ))
    roof = SpatialShedRoof(
        building_id=shell.building_id,
        roof_id=plane.roof_id,
        down_slope_direction=direction,
        placements=placements,
    )
    validate_shed_roof_support(roof, shell)
    return roof
