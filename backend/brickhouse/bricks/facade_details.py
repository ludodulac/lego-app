"""Deterministic facade details that never fake window joinery with wall bricks.

Architectural trim is allowed only outside the glazing void. Observed sills and
decorative surrounds remain separate from frame/pane joinery, and each emitted
cell keeps its architectural role so later LEGO part selection can improve
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


def _to_global(facade: Facade, local_x: int, course: int, width_studs: int, depth_studs: int) -> tuple[int, int, int]:
    z = course * 3
    if facade is Facade.FRONT:
        return local_x, 0, z
    if facade is Facade.REAR:
        return width_studs - local_x - 1, depth_studs - 1, z
    if facade is Facade.RIGHT:
        return width_studs - 1, local_x, z
    return 0, depth_studs - local_x - 1, z


def _append_cell(placements, seen, *, facade, local_x, course, wall_width, wall_height, front_width, depth, opening_id, trim_role) -> None:
    if not (0 <= local_x < wall_width and 0 <= course < wall_height):
        return
    key = (facade, local_x, course)
    if key in seen:
        return
    seen.add(key)
    x, y, z = _to_global(facade, local_x, course, front_width, depth)
    placements.append(FacadeDetailPlacement(part_id="BRICK_1X1", facade=facade, x_studs=x, y_studs=y, z_plates=z, opening_id=opening_id, trim_role=trim_role))


def generate_window_surrounds(building: BuildingModel, shell: BuildingBrickShell, *, skip_opening_ids: set[str] | None = None) -> list[FacadeDetailPlacement]:
    """Render observed sill/surround masonry strictly outside window voids."""
    _ = skip_opening_ids
    openings = {opening.id: opening for opening in building.openings}
    walls = {wall.facade: wall for wall in shell.walls}
    front = walls[Facade.FRONT].grid.width_studs
    depth = walls[Facade.RIGHT].grid.width_studs
    placements: list[FacadeDetailPlacement] = []
    seen: set[tuple[Facade, int, int]] = set()

    def add(facade, raster, local_x, course, role, wall):
        _append_cell(placements, seen, facade=facade, local_x=local_x, course=course, wall_width=wall.grid.width_studs, wall_height=wall.grid.height_bricks, front_width=front, depth=depth, opening_id=raster.id, trim_role=role)

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
                for local_x in range(raster.x_studs, raster.x_studs + raster.width_studs):
                    add(facade, raster, local_x, top, "head", wall)
                if not opening.has_sill:
                    for local_x in range(raster.x_studs, raster.x_studs + raster.width_studs):
                        add(facade, raster, local_x, bottom, "surround_base", wall)
            if opening.has_sill:
                for local_x in range(raster.x_studs, raster.x_studs + raster.width_studs):
                    add(facade, raster, local_x, bottom, "sill", wall)
    return placements
