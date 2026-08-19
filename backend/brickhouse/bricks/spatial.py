"""Global 3D brick placement for a rectangular building shell."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import Facade

from .building_layout import BuildingBrickShell, BuildingWallLayout
from .catalog import create_m0_brick_catalog
from .placement import (
    _BRICK_ID_BY_SPAN,
    _allowed_segments,
    _choose_segment_composition,
)


class GlobalBrickPlacement(BaseModel):
    brick_id: str
    facade: Facade
    x_studs: int = Field(ge=0)
    y_studs: int = Field(ge=0)
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3]


class SpatialBrickShell(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    volume_id: str
    width_studs: int = Field(gt=0)
    depth_studs: int = Field(gt=0)
    height_bricks: int = Field(gt=0)
    placements: list[GlobalBrickPlacement]


def _wall_by_facade(shell: BuildingBrickShell) -> dict[Facade, BuildingWallLayout]:
    by_facade = {record.facade: record for record in shell.walls}
    required = {Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT}
    if set(by_facade) != required:
        raise ValueError("building shell must contain front, rear, left and right walls")
    return by_facade


def _corner_trimmed_segments(
    wall: BuildingWallLayout,
    course: int,
    wall_owns_corners: bool,
) -> list[tuple[int, int]]:
    segments = _allowed_segments(wall.grid.width_studs, course, wall.grid.openings)
    if wall_owns_corners:
        return segments

    width = wall.grid.width_studs
    trimmed: list[tuple[int, int]] = []
    for start, end in segments:
        start = max(start, 1)
        end = min(end, width - 1)
        if start < end:
            trimmed.append((start, end))
    return trimmed


def _course_local_bricks(
    wall: BuildingWallLayout,
    course: int,
    wall_owns_corners: bool,
) -> list[tuple[str, int, int]]:
    """Return (brick_id, local_x, span) for one reconstructed wall course."""
    previous_joints: frozenset[int] = frozenset()
    if course > 0:
        # Corner weaving is the primary structural rule here. Joint staggering
        # remains deterministic within the current course but is not carried
        # across the re-tiled facade in BH-010.
        previous_joints = frozenset()

    result: list[tuple[str, int, int]] = []
    for start, end in _corner_trimmed_segments(wall, course, wall_owns_corners):
        composition = _choose_segment_composition(start, end, previous_joints)
        x = start
        for span in composition:
            result.append((_BRICK_ID_BY_SPAN[span], x, span))
            x += span
    return result


def _to_global(
    facade: Facade,
    local_x: int,
    span: int,
    course: int,
    width_studs: int,
    depth_studs: int,
    brick_id: str,
) -> GlobalBrickPlacement:
    z = course * 3
    if facade is Facade.FRONT:
        return GlobalBrickPlacement(
            brick_id=brick_id,
            facade=facade,
            x_studs=local_x,
            y_studs=0,
            z_plates=z,
            rotation_quarter_turns=1 if span > 1 else 0,
        )
    if facade is Facade.REAR:
        return GlobalBrickPlacement(
            brick_id=brick_id,
            facade=facade,
            x_studs=width_studs - local_x - span,
            y_studs=depth_studs - 1,
            z_plates=z,
            rotation_quarter_turns=1 if span > 1 else 0,
        )
    if facade is Facade.RIGHT:
        return GlobalBrickPlacement(
            brick_id=brick_id,
            facade=facade,
            x_studs=width_studs - 1,
            y_studs=local_x,
            z_plates=z,
            rotation_quarter_turns=0,
        )
    return GlobalBrickPlacement(
        brick_id=brick_id,
        facade=facade,
        x_studs=0,
        y_studs=depth_studs - local_x - span,
        z_plates=z,
        rotation_quarter_turns=0,
    )


def _occupied_cells(placement: GlobalBrickPlacement) -> set[tuple[int, int, int]]:
    brick = create_m0_brick_catalog().get(placement.brick_id)
    fx, fy = brick.footprint(placement.rotation_quarter_turns)
    course = placement.z_plates // 3
    return {
        (placement.x_studs + dx, placement.y_studs + dy, course)
        for dx in range(fx)
        for dy in range(fy)
    }


def generate_spatial_brick_shell(shell: BuildingBrickShell) -> SpatialBrickShell:
    """Place four walls globally and alternate corner ownership by course."""
    by_facade = _wall_by_facade(shell)
    width = by_facade[Facade.FRONT].grid.width_studs
    depth = by_facade[Facade.RIGHT].grid.width_studs
    heights = {record.grid.height_bricks for record in shell.walls}
    if len(heights) != 1:
        raise ValueError("all walls must share one grid height")
    height = next(iter(heights))

    placements: list[GlobalBrickPlacement] = []
    occupied: set[tuple[int, int, int]] = set()

    for course in range(height):
        horizontal_owns = course % 2 == 0
        for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
            wall_owns = horizontal_owns if facade in {Facade.FRONT, Facade.REAR} else not horizontal_owns
            wall = by_facade[facade]
            for brick_id, local_x, span in _course_local_bricks(wall, course, wall_owns):
                placement = _to_global(
                    facade,
                    local_x,
                    span,
                    course,
                    width,
                    depth,
                    brick_id,
                )
                cells = _occupied_cells(placement)
                overlap = occupied.intersection(cells)
                if overlap:
                    raise RuntimeError(f"global brick overlap detected at {sorted(overlap)!r}")
                occupied.update(cells)
                placements.append(placement)

    return SpatialBrickShell(
        building_id=shell.building_id,
        volume_id=shell.volume_id,
        width_studs=width,
        depth_studs=depth,
        height_bricks=height,
        placements=placements,
    )
