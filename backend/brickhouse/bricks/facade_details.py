"""Deterministic facade details that never fake window joinery with wall bricks.

Architectural trim is allowed only outside the glazing void. Observed sills and
decorative surrounds remain separate from frame/pane joinery, and each emitted
placement keeps its architectural role so later LEGO part selection can improve
without changing the evidence model.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel, Facade, OpeningType
from .building_layout import BuildingBrickShell

TrimRole = Literal["sill", "left_jamb", "right_jamb", "head", "surround_base"]


class FacadeDetailPlacement(BaseModel):
    part_id: str
    category: Literal["facade_detail"] = "facade_detail"
    facade: Facade
    x_studs: int = Field(ge=0)
    y_studs: int = Field(ge=0)
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3] = 0
    opening_id: str | None = None
    trim_role: TrimRole | None = None


_CANONICAL_TRIM_SPANS: tuple[tuple[int, str], ...] = (
    (8, "BRICK_1X8"),
    (6, "BRICK_1X6"),
    (4, "BRICK_1X4"),
    (3, "BRICK_1X3"),
    (2, "BRICK_1X2"),
    (1, "BRICK_1X1"),
)


def _to_global(
    facade: Facade,
    local_x: int,
    course: int,
    width_studs: int,
    depth_studs: int,
) -> tuple[int, int, int]:
    z = course * 3
    if facade is Facade.FRONT:
        return local_x, 0, z
    if facade is Facade.REAR:
        return width_studs - local_x - 1, depth_studs - 1, z
    if facade is Facade.RIGHT:
        return width_studs - 1, local_x, z
    return 0, depth_studs - local_x - 1, z


def _to_global_horizontal_run(
    facade: Facade,
    local_x: int,
    span: int,
    course: int,
    width_studs: int,
    depth_studs: int,
) -> tuple[int, int, int, Literal[0, 1]]:
    """Map one facade-local horizontal run to a canonical 1xN brick anchor.

    The anchor is always the minimum world-grid corner of the brick footprint.
    Rear and left facades reverse their local horizontal axis, so their anchor
    must account for the full span rather than only the first local cell.
    """
    z = course * 3
    if facade is Facade.FRONT:
        return local_x, 0, z, 1
    if facade is Facade.REAR:
        return width_studs - local_x - span, depth_studs - 1, z, 1
    if facade is Facade.RIGHT:
        return width_studs - 1, local_x, z, 0
    return 0, depth_studs - local_x - span, z, 0


def _append_cell(
    placements,
    seen,
    *,
    facade,
    local_x,
    course,
    wall_width,
    wall_height,
    front_width,
    depth,
    opening_id,
    trim_role,
) -> None:
    if not (0 <= local_x < wall_width and 0 <= course < wall_height):
        return
    key = (facade, local_x, course)
    if key in seen:
        return
    seen.add(key)
    x, y, z = _to_global(facade, local_x, course, front_width, depth)
    placements.append(
        FacadeDetailPlacement(
            part_id="BRICK_1X1",
            facade=facade,
            x_studs=x,
            y_studs=y,
            z_plates=z,
            opening_id=opening_id,
            trim_role=trim_role,
        )
    )


def _append_horizontal_run(
    placements,
    seen,
    *,
    facade,
    start_local_x,
    end_local_x,
    course,
    wall_width,
    wall_height,
    front_width,
    depth,
    opening_id,
    trim_role,
) -> None:
    """Compact an exact horizontal cell run into longest canonical 1xN bricks."""
    start = max(0, start_local_x)
    end = min(wall_width, end_local_x)
    if start >= end or not (0 <= course < wall_height):
        return

    cursor = start
    while cursor < end:
        remaining = end - cursor
        for span, part_id in _CANONICAL_TRIM_SPANS:
            if span > remaining:
                continue
            cells = [(facade, local_x, course) for local_x in range(cursor, cursor + span)]
            if any(cell in seen for cell in cells):
                # Existing semantic trim owns at least one cell. Fall back to a
                # single cell so overlap handling remains identical to the old
                # 1x1 implementation instead of spanning across owned geometry.
                span, part_id = 1, "BRICK_1X1"
                cells = [(facade, cursor, course)]
            if cells[0] in seen:
                cursor += 1
                break

            seen.update(cells)
            x, y, z, rotation = _to_global_horizontal_run(
                facade,
                cursor,
                span,
                course,
                front_width,
                depth,
            )
            placements.append(
                FacadeDetailPlacement(
                    part_id=part_id,
                    facade=facade,
                    x_studs=x,
                    y_studs=y,
                    z_plates=z,
                    rotation_quarter_turns=rotation if span > 1 else 0,
                    opening_id=opening_id,
                    trim_role=trim_role,
                )
            )
            cursor += span
            break


def generate_window_surrounds(
    building: BuildingModel,
    shell: BuildingBrickShell,
    *,
    skip_opening_ids: set[str] | None = None,
) -> list[FacadeDetailPlacement]:
    """Render observed sill/surround masonry strictly outside window voids.

    Horizontal sill/head/base runs use the longest placement-approved canonical
    1xN bricks that preserve the exact occupied cells. Vertical jambs remain
    1x1-per-course because the current placement model supports only rotations
    around the vertical axis; using a 1xN brick across courses would invent an
    unvalidated sideways-building technique.
    """
    _ = skip_opening_ids
    openings = {opening.id: opening for opening in building.openings}
    walls = {wall.facade: wall for wall in shell.walls}
    front = walls[Facade.FRONT].grid.width_studs
    depth = walls[Facade.RIGHT].grid.width_studs
    placements: list[FacadeDetailPlacement] = []
    seen: set[tuple[Facade, int, int]] = set()

    def add(facade, raster, local_x, course, role, wall):
        _append_cell(
            placements,
            seen,
            facade=facade,
            local_x=local_x,
            course=course,
            wall_width=wall.grid.width_studs,
            wall_height=wall.grid.height_bricks,
            front_width=front,
            depth=depth,
            opening_id=raster.id,
            trim_role=role,
        )

    def add_run(facade, raster, start, end, course, role, wall):
        _append_horizontal_run(
            placements,
            seen,
            facade=facade,
            start_local_x=start,
            end_local_x=end,
            course=course,
            wall_width=wall.grid.width_studs,
            wall_height=wall.grid.height_bricks,
            front_width=front,
            depth=depth,
            opening_id=raster.id,
            trim_role=role,
        )

    for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
        wall = walls[facade]
        for raster in wall.grid.openings:
            opening = openings.get(raster.id)
            if not opening or opening.type is not OpeningType.WINDOW:
                continue
            if not opening.has_sill and not opening.has_decorative_surround:
                continue
            left = raster.x_studs - 1
            right = raster.x_studs + raster.width_studs
            bottom = raster.z_bricks - 1
            top = raster.z_bricks + raster.height_bricks
            if opening.has_decorative_surround:
                for course in range(raster.z_bricks, raster.z_bricks + raster.height_bricks):
                    add(facade, raster, left, course, "left_jamb", wall)
                    add(facade, raster, right, course, "right_jamb", wall)
                add_run(
                    facade,
                    raster,
                    raster.x_studs,
                    raster.x_studs + raster.width_studs,
                    top,
                    "head",
                    wall,
                )
                if not opening.has_sill:
                    add_run(
                        facade,
                        raster,
                        raster.x_studs,
                        raster.x_studs + raster.width_studs,
                        bottom,
                        "surround_base",
                        wall,
                    )
            if opening.has_sill:
                add_run(
                    facade,
                    raster,
                    raster.x_studs,
                    raster.x_studs + raster.width_studs,
                    bottom,
                    "sill",
                    wall,
                )
    return placements
