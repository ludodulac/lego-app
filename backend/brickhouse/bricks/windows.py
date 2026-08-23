"""Validated real LEGO window assemblies for BrickHouse.

BrickHouse prefers explicit frame+pane assemblies over masonry drawn inside a
window opening. Larger rectangular windows may be tiled with several validated
assemblies when (and only when) the rasterized opening can be covered exactly.
This keeps the opening transparent and constructible instead of inserting wall
bricks as fake mullions.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel, Facade, OpeningType, WindowStyle
from .building_layout import BuildingBrickShell


@dataclass(frozen=True)
class WindowAssemblyDefinition:
    id: str
    frame_part_id: str
    pane_part_id: str
    width_studs: int
    height_bricks: int


VALIDATED_WINDOW_ASSEMBLIES: tuple[WindowAssemblyDefinition, ...] = (
    WindowAssemblyDefinition("window-1x2x2-60592-60601", "WINDOW_1X2X2_60592", "GLASS_FOR_WINDOW_1X2X2_60601", 2, 2),
    WindowAssemblyDefinition("window-1x2x3-60593-60602", "WINDOW_1X2X3_60593", "GLASS_FOR_WINDOW_1X2X3_60602", 2, 3),
    WindowAssemblyDefinition("window-1x4x3-60594-60603", "WINDOW_1X4X3_60594", "GLASS_FOR_WINDOW_1X4X3_60603", 4, 3),
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
    opening_width: int,
    z_bricks: int,
    width_studs: int,
    depth_studs: int,
) -> tuple[int, int, int, Literal[0, 1, 2, 3]]:
    z = z_bricks * 3
    if facade is Facade.FRONT:
        return local_x, 0, z, 1
    if facade is Facade.REAR:
        return width_studs - local_x - opening_width, depth_studs - 1, z, 1
    if facade is Facade.RIGHT:
        return width_studs - 1, local_x, z, 0
    return 0, depth_studs - local_x - opening_width, z, 0


def choose_window_assembly(width_studs: int, height_bricks: int) -> WindowAssemblyDefinition | None:
    return next(
        (assembly for assembly in VALIDATED_WINDOW_ASSEMBLIES if assembly.width_studs == width_studs and assembly.height_bricks == height_bricks),
        None,
    )


@lru_cache(maxsize=None)
def _height_partition(total: int, preferred: tuple[int, ...]) -> tuple[int, ...] | None:
    if total == 0:
        return ()
    if total < 0:
        return None
    for size in preferred:
        tail = _height_partition(total - size, preferred)
        if tail is not None:
            return (size, *tail)
    return None


def _row_layout(width_studs: int, height_bricks: int, *, paired: bool) -> tuple[tuple[WindowAssemblyDefinition, int], ...] | None:
    candidates = sorted(
        (assembly for assembly in VALIDATED_WINDOW_ASSEMBLIES if assembly.height_bricks == height_bricks),
        key=lambda assembly: assembly.width_studs,
        reverse=True,
    )
    if paired:
        candidates = [assembly for assembly in candidates if assembly.width_studs == 2]
    if not candidates:
        return None

    @lru_cache(maxsize=None)
    def solve(remaining: int) -> tuple[WindowAssemblyDefinition, ...] | None:
        if remaining == 0:
            return ()
        if remaining < 0:
            return None
        for assembly in candidates:
            tail = solve(remaining - assembly.width_studs)
            if tail is not None:
                return (assembly, *tail)
        return None

    assemblies = solve(width_studs)
    if assemblies is None:
        return None
    cursor = 0
    result = []
    for assembly in assemblies:
        result.append((assembly, cursor))
        cursor += assembly.width_studs
    return tuple(result)


def choose_window_layout(
    style: WindowStyle,
    width_studs: int,
    height_bricks: int,
) -> tuple[tuple[WindowAssemblyDefinition, int, int], ...]:
    """Cover a rasterized opening exactly with validated LEGO frame/pane pairs.

    No stretching and no partial cover is allowed. If the exact rectangle cannot
    be tiled by the validated catalogue, return an empty layout and let the
    facade-detail fallback handle only the perimeter.
    """
    if style in {WindowStyle.FOUR_PANE, WindowStyle.BAY}:
        return ()

    if style is WindowStyle.TRADITIONAL_TALL:
        heights = _height_partition(height_bricks, (3,))
    else:
        # Prefer 3-brick modules, then 2-brick modules. This minimizes horizontal
        # joins while still covering taller residential windows exactly.
        heights = _height_partition(height_bricks, (3, 2))
    if heights is None:
        return ()

    paired = style is WindowStyle.PAIRED
    result: list[tuple[WindowAssemblyDefinition, int, int]] = []
    z_offset = 0
    for row_height in heights:
        row = _row_layout(width_studs, row_height, paired=paired)
        if row is None:
            return ()
        for assembly, x_offset in row:
            result.append((assembly, x_offset, z_offset))
        z_offset += row_height
    return tuple(result)


def _emit_pair(
    placements: list[WindowPartPlacement],
    assembly: WindowAssemblyDefinition,
    facade: Facade,
    local_x: int,
    z_bricks: int,
    front: int,
    depth: int,
) -> None:
    x, y, z, rotation = _to_global(facade, local_x, assembly.width_studs, z_bricks, front, depth)
    placements.extend((
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
    ))


def generate_window_assemblies(
    building: BuildingModel,
    shell: BuildingBrickShell,
) -> tuple[list[WindowPartPlacement], set[str]]:
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
            style = opening.window_style or WindowStyle.SIMPLE
            layout = choose_window_layout(style, raster.width_studs, raster.height_bricks)
            if not layout:
                continue
            for assembly, x_offset, z_offset in layout:
                _emit_pair(
                    placements,
                    assembly,
                    facade,
                    raster.x_studs + x_offset,
                    raster.z_bricks + z_offset,
                    front,
                    depth,
                )
            fitted.add(raster.id)
    return placements, fitted
