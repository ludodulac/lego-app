"""Deterministic facade-detail placements built from supported standard bricks."""

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


def generate_window_surrounds(
    building: BuildingModel,
    shell: BuildingBrickShell,
) -> list[FacadeDetailPlacement]:
    """Create a simple inset frame around each window using canonical BRICK_1X1 parts.

    The frame occupies cells that were already removed from the wall opening, so it
    remains constructible without overlapping the structural shell. This is the
    first catalog-backed window style; transparent panes and richer frame families
    can be layered on later.
    """
    opening_types = {opening.id: opening.type for opening in building.openings}
    walls = {wall.facade: wall for wall in shell.walls}
    front = walls[Facade.FRONT].grid.width_studs
    depth = walls[Facade.RIGHT].grid.width_studs
    placements: list[FacadeDetailPlacement] = []

    for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
        wall = walls[facade]
        for opening in wall.grid.openings:
            if opening_types.get(opening.id) is not OpeningType.WINDOW:
                continue
            if opening.width_studs < 3 or opening.height_bricks < 3:
                continue

            x0 = opening.x_studs
            x1 = opening.x_studs + opening.width_studs - 1
            z0 = opening.z_bricks
            z1 = opening.z_bricks + opening.height_bricks - 1
            cells: set[tuple[int, int]] = set()

            for course in range(z0, z1 + 1):
                cells.add((x0, course))
                cells.add((x1, course))
            for local_x in range(x0 + 1, x1):
                cells.add((local_x, z0))
                cells.add((local_x, z1))

            for local_x, course in sorted(cells, key=lambda item: (item[1], item[0])):
                x, y, z = _to_global(facade, local_x, course, front, depth)
                placements.append(
                    FacadeDetailPlacement(
                        part_id="BRICK_1X1",
                        facade=facade,
                        x_studs=x,
                        y_studs=y,
                        z_plates=z,
                    )
                )

    return placements
