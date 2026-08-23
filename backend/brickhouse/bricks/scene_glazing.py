"""Scene-aware glazing for openings not represented by the basic window catalogue.

Validated standard LEGO window assemblies remain the preferred representation for
ordinary windows. This module handles two architectural cases carried only by the
rich Scene today: glass-block openings and explicitly glazed doors/French doors.
It uses transparent 1x1 brick cells plus frame cells so these openings remain
visibly glazed instead of becoming empty holes or masonry bars.
"""
from __future__ import annotations

import unicodedata

from brickhouse.building.models import Facade, OpeningType
from brickhouse.scene.models import ArchitecturalScene, SceneOpening

from .brick_model import BrickModel, BrickModelPart
from .scaling import COURSES_PER_STUD_RATIO
from .scene_architecture import _round_half_up, _scene_bounds


def _normalized(value: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower().split()
    )


def _opening_text(opening: SceneOpening) -> str:
    evidence = " ".join(item.observation for item in opening.evidence)
    return _normalized(f"{opening.id} {evidence}")


def _is_glass_block(opening: SceneOpening) -> bool:
    text = _opening_text(opening)
    return any(token in text for token in ("paves de verre", "pave de verre", "glass block", "glass-block"))


def _is_glazed_door(opening: SceneOpening) -> bool:
    if opening.type is not OpeningType.DOOR:
        return False
    text = _opening_text(opening)
    return any(token in text for token in ("porte-fenetre", "porte fenetre", "glazed", "vitree", "vitrage"))


def _part(
    placement_id: str,
    *,
    x: int,
    y: int,
    z: int,
    facade: Facade,
    category: str,
    rotation: int,
) -> BrickModelPart:
    return BrickModelPart(
        placement_id=placement_id,
        part_id="BRICK_1X1",
        category=category,
        component="facade_detail",
        x_studs=max(0, x),
        y_studs=max(0, y),
        z_plates=max(0, z),
        rotation_quarter_turns=rotation,
        facade=facade,
    )


def _opening_grid(
    opening: SceneOpening,
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> tuple[int, int, int, int, int, int]:
    main = scene.volumes[0]
    courses_per_meter = studs_per_meter * COURSES_PER_STUD_RATIO
    house_x = _round_half_up((main.position.x - origin_x) * studs_per_meter)
    house_y = _round_half_up((main.position.y - origin_y) * studs_per_meter)
    house_width = max(1, _round_half_up(main.width.value * studs_per_meter))
    house_depth = max(1, _round_half_up(main.depth.value * studs_per_meter))
    local = max(0, _round_half_up(opening.offset_horizontal * studs_per_meter))
    z0 = max(0, _round_half_up(opening.offset_vertical * courses_per_meter))
    width = max(1, _round_half_up(opening.width * studs_per_meter))
    height = max(1, _round_half_up(opening.height * courses_per_meter))
    return house_x, house_y, house_width, house_depth, local, z0, width, height


def _global_cell(
    facade: Facade,
    *,
    house_x: int,
    house_y: int,
    house_width: int,
    house_depth: int,
    local_x: int,
    opening_width: int,
    z_course: int,
) -> tuple[int, int, int, int]:
    z = z_course * 3
    if facade is Facade.FRONT:
        return house_x + local_x, house_y, z, 1
    if facade is Facade.REAR:
        return house_x + house_width - local_x - opening_width, house_y + house_depth - 1, z, 1
    if facade is Facade.RIGHT:
        return house_x + house_width - 1, house_y + local_x, z, 0
    return house_x, house_y + house_depth - local_x - opening_width, z, 0


def _opening_parts(
    opening: SceneOpening,
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> list[BrickModelPart]:
    glass_blocks = _is_glass_block(opening)
    glazed_door = _is_glazed_door(opening)
    if not glass_blocks and not glazed_door:
        return []

    house_x, house_y, house_width, house_depth, local, z0, width, height = _opening_grid(
        opening, scene, origin_x=origin_x, origin_y=origin_y, studs_per_meter=studs_per_meter
    )
    parts: list[BrickModelPart] = []
    index = 1
    for dx in range(width):
        for dz in range(height):
            # French/glazed doors get a one-cell frame around transparent cells.
            # Glass blocks remain transparent cells across the whole opening.
            is_frame = glazed_door and (dx in {0, width - 1} or dz in {0, height - 1})
            category = "window_frame" if is_frame else "window_pane"
            local_x = local + dx
            gx, gy, gz, rotation = _global_cell(
                opening.facade,
                house_x=house_x,
                house_y=house_y,
                house_width=house_width,
                house_depth=house_depth,
                local_x=local_x,
                opening_width=1,
                z_course=z0 + dz,
            )
            parts.append(_part(
                f"scene-glazing:{opening.id}:{index:05d}",
                x=gx, y=gy, z=gz, facade=opening.facade,
                category=category, rotation=rotation,
            ))
            index += 1
    return parts


def augment_brick_model_with_scene_glazing(
    model: BrickModel,
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> BrickModel:
    """Add glass blocks and explicitly glazed doors from the rich Scene."""
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")
    targets = [opening for opening in scene.openings if _is_glass_block(opening) or _is_glazed_door(opening)]
    if not targets:
        return model

    main = scene.volumes[0]
    studs_per_meter = front_width_studs / main.width.value
    origin_x, origin_y, _ = _scene_bounds(scene)
    extra: list[BrickModelPart] = []
    for opening in targets:
        extra.extend(_opening_parts(
            opening, scene,
            origin_x=origin_x,
            origin_y=origin_y,
            studs_per_meter=studs_per_meter,
        ))
    if not extra:
        return model
    return model.model_copy(update={"parts": [*model.parts, *extra]})
