"""Validated real LEGO window assemblies for BrickHouse.

Compatibility is explicit: a pane is never paired to a frame by name similarity.
The initial family is backed by catalog compatibility for frame 60594 and pane 60603.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel, Facade, OpeningType
from .building_layout import BuildingBrickShell


@dataclass(frozen=True)
class WindowAssemblyDefinition:
    id: str
    frame_part_id: str
    pane_part_id: str
    width_studs: int
    height_bricks: int


VALIDATED_WINDOW_ASSEMBLIES: tuple[WindowAssemblyDefinition, ...] = (
    WindowAssemblyDefinition(
        id="window-1x4x3-60594-60603",
        frame_part_id="WINDOW_1X4X3_60594",
        pane_part_id="GLASS_FOR_WINDOW_1X4X3_60603",
        width_studs=4,
        height_bricks=3,
    ),
)


class WindowPartPlacement(BaseModel):
    part_id: str
    category: Literal["window_frame", "window_pane"]
    facade: Facade
    x_studs: int = Field(ge=0)
    y_studs: int = Field(ge=0)
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3] = 0


def _to_global(
    facade: Facade,
    local_x: int,
    z_bricks: int,
    width_studs: int,
    depth_studs: int,
) -> tuple[int, int, int, Literal[0, 1, 2, 3]]:
    z = z_bricks * 3
    if facade is Facade.FRONT:
        return local_x, 0, z, 0
    if facade is Facade.REAR:
        return width_studs - local_x - 1, depth_studs - 1, z, 0
    if facade is Facade.RIGHT:
        return width_studs - 1, local_x, z, 1
    return 0, depth_studs - local_x - 1, z, 1


def choose_window_assembly(width_studs: int, height_bricks: int) -> WindowAssemblyDefinition | None:
    """Return a validated assembly only for an exact rasterized opening fit."""
    return next(
        (
            assembly
            for assembly in VALIDATED_WINDOW_ASSEMBLIES
            if assembly.width_studs == width_studs and assembly.height_bricks == height_bricks
        ),
        None,
    )


def generate_window_assemblies(
    building: BuildingModel,
    shell: BuildingBrickShell,
) -> tuple[list[WindowPartPlacement], set[str]]:
    """Emit real frame+pane pairs for openings with a validated exact fit.

    The returned opening-id set lets masonry generation preserve its existing
    fallback for every opening that has no validated assembly.
    """
    openings = {opening.id: opening for opening in building.openings}
    walls = {wall.facade: wall for wall in shell.walls}
    front = walls[Facade.FRONT].grid.width_studs
    depth = walls[Facade.RIGHT].grid.width_studs
    placements: list[WindowPartPlacement] = []
    fitted: set[str] = set()

    for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
        for raster in walls[facade].grid.openings:
            opening = openings.get(raster.id)
            if not opening or opening.type is not OpeningType.WINDOW:
                continue
            assembly = choose_window_assembly(raster.width_studs, raster.height_bricks)
            if assembly is None:
                continue
            x, y, z, rotation = _to_global(facade, raster.x_studs, raster.z_bricks, front, depth)
            placements.extend(
                (
                    WindowPartPlacement(
                        part_id=assembly.frame_part_id,
                        category="window_frame",
                        facade=facade,
                        x_studs=x,
                        y_studs=y,
                        z_plates=z,
                        rotation_quarter_turns=rotation,
                    ),
                    WindowPartPlacement(
                        part_id=assembly.pane_part_id,
                        category="window_pane",
                        facade=facade,
                        x_studs=x,
                        y_studs=y,
                        z_plates=z,
                        rotation_quarter_turns=rotation,
                    ),
                )
            )
            fitted.add(raster.id)
    return placements, fitted
