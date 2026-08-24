"""Validated real LEGO window assemblies for BrickHouse.

BrickHouse prefers explicit frame+pane assemblies over masonry drawn inside a
window opening. Window composition is architectural evidence: a larger opening
must not be tiled with several frames merely because that makes it constructible.
Only a Scene style that explicitly implies subdivisions may create them.

When a simple planar window has no exact validated frame family, BrickHouse may
fill the already-preserved opening with transparent standard 1x1 bricks. Those
cells are LEGO discretization, not architectural mullions: no opaque cross-bar or
invented subdivision is added.
"""
from __future__ import annotations

from dataclasses import dataclass
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
    WindowAssemblyDefinition(
        "window-1x2x2-60592-60601",
        "WINDOW_1X2X2_60592",
        "GLASS_FOR_WINDOW_1X2X2_60601",
        2,
        2,
    ),
    WindowAssemblyDefinition(
        "window-1x2x3-60593-60602",
        "WINDOW_1X2X3_60593",
        "GLASS_FOR_WINDOW_1X2X3_60602",
        2,
        3,
    ),
    WindowAssemblyDefinition(
        "window-1x4x3-60594-60603",
        "WINDOW_1X4X3_60594",
        "GLASS_FOR_WINDOW_1X4X3_60603",
        4,
        3,
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


def choose_window_assembly(
    width_studs: int,
    height_bricks: int,
) -> WindowAssemblyDefinition | None:
    return next(
        (
            assembly
            for assembly in VALIDATED_WINDOW_ASSEMBLIES
            if assembly.width_studs == width_studs
            and assembly.height_bricks == height_bricks
        ),
        None,
    )


def _assembly(width: int, height: int) -> WindowAssemblyDefinition | None:
    return choose_window_assembly(width, height)


def choose_window_layout(
    style: WindowStyle,
    width_studs: int,
    height_bricks: int,
) -> tuple[tuple[WindowAssemblyDefinition, int, int], ...]:
    """Fit validated LEGO frames without inventing architectural joinery."""
    if style is WindowStyle.BAY:
        return ()

    if style is WindowStyle.SIMPLE:
        assembly = _assembly(width_studs, height_bricks)
        return ((assembly, 0, 0),) if assembly is not None else ()

    if style is WindowStyle.TRADITIONAL_TALL:
        # A 2x2 frame is dimensionally possible but contradicts the semantic
        # style. Keep the original style-aware contract: only the validated
        # three-brick-high module is a real traditional-tall assembly.
        assembly = _assembly(2, 3) if width_studs == 2 and height_bricks == 3 else None
        return ((assembly, 0, 0),) if assembly is not None else ()

    if style is WindowStyle.PAIRED:
        if width_studs != 4 or height_bricks not in {2, 3}:
            return ()
        assembly = _assembly(2, height_bricks)
        if assembly is None:
            return ()
        return ((assembly, 0, 0), (assembly, 2, 0))

    if style is WindowStyle.FOUR_PANE:
        if width_studs != 4 or height_bricks not in {4, 6}:
            return ()
        pane_height = height_bricks // 2
        assembly = _assembly(2, pane_height)
        if assembly is None:
            return ()
        return (
            (assembly, 0, 0),
            (assembly, 2, 0),
            (assembly, 0, pane_height),
            (assembly, 2, pane_height),
        )

    return ()


def _emit_pair(
    placements: list[WindowPartPlacement],
    assembly: WindowAssemblyDefinition,
    facade: Facade,
    local_x: int,
    z_bricks: int,
    front: int,
    depth: int,
) -> None:
    x, y, z, rotation = _to_global(
        facade,
        local_x,
        assembly.width_studs,
        z_bricks,
        front,
        depth,
    )
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


def _emit_joinery_free_glazing(
    placements: list[WindowPartPlacement],
    *,
    facade: Facade,
    local_x: int,
    z_bricks: int,
    width_studs: int,
    height_bricks: int,
    front: int,
    depth: int,
) -> None:
    """Fill a simple opening with transparent 1x1 LEGO bricks, no fake frame bars."""
    for dx in range(width_studs):
        for dz in range(height_bricks):
            x, y, z, rotation = _to_global(
                facade,
                local_x + dx,
                1,
                z_bricks + dz,
                front,
                depth,
            )
            placements.append(
                WindowPartPlacement(
                    part_id="BRICK_1X1",
                    category="window_pane",
                    facade=facade,
                    x_studs=x,
                    y_studs=y,
                    z_plates=z,
                    rotation_quarter_turns=rotation,
                )
            )


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
            layout = choose_window_layout(
                style,
                raster.width_studs,
                raster.height_bricks,
            )
            if layout:
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
                continue

            # For a visually continuous planar window, a transparent LEGO-brick
            # infill is more faithful than an empty hole and does not assert any
            # mullion/transom geometry. Complex styles remain unsupported rather
            # than being flattened into this fallback.
            if style in {WindowStyle.SIMPLE, WindowStyle.TRADITIONAL_TALL}:
                _emit_joinery_free_glazing(
                    placements,
                    facade=facade,
                    local_x=raster.x_studs,
                    z_bricks=raster.z_bricks,
                    width_studs=raster.width_studs,
                    height_bricks=raster.height_bricks,
                    front=front,
                    depth=depth,
                )
                fitted.add(raster.id)

    return placements, fitted
