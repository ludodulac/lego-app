"""Deterministic facade details that never fake window joinery with wall bricks.

Architectural trim is allowed only outside the glazing void. In particular,
observed sills and decorative surrounds are preserved even when a real LEGO
frame+pane assembly fits the opening. Internal mullions/transoms are handled by
window assemblies, never by masonry fallback geometry.
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field
from brickhouse.building.models import BuildingModel, Facade, OpeningType
from .building_layout import BuildingBrickShell


class FacadeDetailPlacement(BaseModel):
    part_id: str
    category: Literal["facade_detail"] = "facade_detail"
    facade: Facade
    x_studs: int = Field(ge=0)
    y_studs: int = Field(ge=0)
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3] = 0


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


def _append_cell(
    placements: list[FacadeDetailPlacement],
    seen: set[tuple[Facade, int, int]],
    *,
    facade: Facade,
    local_x: int,
    course: int,
    wall_width: int,
    wall_height: int,
    front_width: int,
    depth: int,
) -> None:
    """Append one trim cell only when it lies on the wall, never in the opening."""
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
        )
    )


def generate_window_surrounds(
    building: BuildingModel,
    shell: BuildingBrickShell,
    *,
    skip_opening_ids: set[str] | None = None,
) -> list[FacadeDetailPlacement]:
    """Render observed sill/surround masonry strictly outside window voids.

    ``skip_opening_ids`` is retained for API compatibility with the window
    assembly pipeline. A fitted LEGO frame must *not* erase architectural trim,
    so fitted IDs are no longer skipped when ``has_sill`` or
    ``has_decorative_surround`` is explicitly true.

    Decorative surrounds are represented as a one-stud ring immediately around
    the rasterized opening: side jambs and head, plus a bottom course when no
    explicit sill is requested. Cells that would fall beyond the wall boundary
    are omitted instead of moving or shrinking the opening.
    """
    _ = skip_opening_ids  # compatibility only; architectural metadata wins
    openings = {opening.id: opening for opening in building.openings}
    walls = {wall.facade: wall for wall in shell.walls}
    front = walls[Facade.FRONT].grid.width_studs
    depth = walls[Facade.RIGHT].grid.width_studs
    placements: list[FacadeDetailPlacement] = []
    seen: set[tuple[Facade, int, int]] = set()

    for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
        wall = walls[facade]
        wall_width = wall.grid.width_studs
        wall_height = wall.grid.height_bricks
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
                    _append_cell(
                        placements,
                        seen,
                        facade=facade,
                        local_x=left,
                        course=course,
                        wall_width=wall_width,
                        wall_height=wall_height,
                        front_width=front,
                        depth=depth,
                    )
                    _append_cell(
                        placements,
                        seen,
                        facade=facade,
                        local_x=right,
                        course=course,
                        wall_width=wall_width,
                        wall_height=wall_height,
                        front_width=front,
                        depth=depth,
                    )
                for local_x in range(raster.x_studs, raster.x_studs + raster.width_studs):
                    _append_cell(
                        placements,
                        seen,
                        facade=facade,
                        local_x=local_x,
                        course=top,
                        wall_width=wall_width,
                        wall_height=wall_height,
                        front_width=front,
                        depth=depth,
                    )
                if not opening.has_sill:
                    for local_x in range(raster.x_studs, raster.x_studs + raster.width_studs):
                        _append_cell(
                            placements,
                            seen,
                            facade=facade,
                            local_x=local_x,
                            course=bottom,
                            wall_width=wall_width,
                            wall_height=wall_height,
                            front_width=front,
                            depth=depth,
                        )

            if opening.has_sill:
                for local_x in range(raster.x_studs, raster.x_studs + raster.width_studs):
                    _append_cell(
                        placements,
                        seen,
                        facade=facade,
                        local_x=local_x,
                        course=bottom,
                        wall_width=wall_width,
                        wall_height=wall_height,
                        front_width=front,
                        depth=depth,
                    )

    return placements
