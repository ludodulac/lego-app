"""Integrate a validated mono-pitch LEGO roof without leaving the shell open."""
from __future__ import annotations

from brickhouse.building.models import Facade

from .brick_model import BrickModel, BrickModelPart
from .roof import create_m0_roof_catalog
from .shed_roof import SpatialShedRoof
from .spatial import SpatialBrickShell


def _footprint(placement) -> set[tuple[int, int]]:
    definition = create_m0_roof_catalog().get(placement.part_id)
    width, depth = (
        (definition.length_studs, definition.width_studs)
        if placement.rotation_quarter_turns % 2
        else (definition.width_studs, definition.length_studs)
    )
    return {
        (placement.x_studs + dx, placement.y_studs + dy)
        for dx in range(width)
        for dy in range(depth)
    }


def _boundary_cells(shell: SpatialBrickShell):
    for x in range(shell.width_studs):
        yield Facade.FRONT, x, 0
        yield Facade.REAR, x, shell.depth_studs - 1
    for y in range(1, max(1, shell.depth_studs - 1)):
        yield Facade.LEFT, 0, y
        yield Facade.RIGHT, shell.width_studs - 1, y


def augment_brick_model_with_shed_roof(
    model: BrickModel,
    shell: SpatialBrickShell,
    roof: SpatialShedRoof,
) -> BrickModel:
    """Add roof slopes and the wall infill below their stepped underside.

    The infill height comes from actual placed roof footprints, not from a
    benchmark-specific formula. This closes the high wall and both side wedges
    for all four down-slope orientations.
    """
    if model.building_id != roof.building_id or model.building_id != shell.building_id:
        raise ValueError("shed roof, BrickModel and shell must reference the same building")
    if model.volume_id != shell.volume_id:
        raise ValueError("shed roof integration requires the BrickModel shell volume")

    coverage: dict[tuple[int, int], list[int]] = {}
    for placement in roof.placements:
        for cell in _footprint(placement):
            coverage.setdefault(cell, []).append(placement.z_plates)

    wall_top = shell.height_bricks * 3
    additions: list[BrickModelPart] = []
    wall_index = 1
    for facade, x, y in _boundary_cells(shell):
        z_values = coverage.get((x, y))
        if not z_values:
            raise ValueError(
                f"shed roof leaves facade {facade.value} boundary cell ({x}, {y}) uncovered"
            )
        underside = min(z_values)
        if underside < wall_top or (underside - wall_top) % 3:
            raise ValueError("shed roof underside is incompatible with brick-course wall infill")
        for z in range(wall_top, underside, 3):
            additions.append(
                BrickModelPart(
                    placement_id=f"shed-wall-{wall_index:06d}",
                    part_id="BRICK_1X1",
                    category="brick",
                    component="wall",
                    x_studs=x,
                    y_studs=y,
                    z_plates=z,
                    rotation_quarter_turns=0,
                    facade=facade,
                )
            )
            wall_index += 1

    orientation = {
        Facade.LEFT: 0,
        Facade.REAR: 1,
        Facade.RIGHT: 2,
        Facade.FRONT: 3,
    }[roof.down_slope_direction]
    catalog = create_m0_roof_catalog()
    for index, placement in enumerate(roof.placements, start=1):
        definition = catalog.get(placement.part_id)
        if definition.category != "roof_tile":
            raise ValueError("shed roof may only contain validated slope roof tiles")
        additions.append(
            BrickModelPart(
                placement_id=f"shed-roof-{index:06d}",
                part_id=placement.part_id,
                category="roof_tile",
                component="roof",
                x_studs=placement.x_studs,
                y_studs=placement.y_studs,
                z_plates=placement.z_plates,
                rotation_quarter_turns=orientation,
                roof_side="slope",
            )
        )

    roof_top = max(
        placement.z_plates + catalog.get(placement.part_id).height_plates
        for placement in roof.placements
    )
    return model.model_copy(
        update={
            "height_plates": max(model.height_plates, roof_top),
            "parts": [*model.parts, *additions],
        }
    )
