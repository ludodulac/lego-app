"""Scene-aware final detail augmentation for glazing and metric chimneys."""
from __future__ import annotations

import unicodedata

from brickhouse.building.models import Facade, OpeningType
from brickhouse.scene import ArchitecturalScene
from brickhouse.scene.models import SceneOpening
from .brick_model import BrickModel, BrickModelPart
from .scaling import COURSES_PER_STUD_RATIO
from .scene_architecture import _round_half_up, _scene_bounds
from .scene_chimneys import augment_brick_model_with_scene_chimneys
from .wall_depth import augment_brick_model_with_wall_depth


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower().split())


def _opening_text(opening: SceneOpening) -> str:
    evidence = " ".join(item.observation for item in opening.evidence)
    return _normalized(f"{opening.id} {evidence}")


def _is_glass_block(opening: SceneOpening) -> bool:
    text = _opening_text(opening)
    return any(token in text for token in ("paves de verre", "pave de verre", "glass block", "glass-block"))


def _structured_glazing_state(opening: SceneOpening) -> bool | None:
    """Return a structured glazing decision, or None when no such evidence exists.

    A populated ``opening_visual.glazing`` field is authoritative. Explicitly
    negative or unknown values therefore suppress the legacy prose heuristic
    rather than allowing unrelated evidence text to re-invent glazing.
    """
    if opening.opening_visual is None or opening.opening_visual.glazing is None:
        return None
    value = _normalized(opening.opening_visual.glazing)
    if not value:
        return False

    negative = (
        "none",
        "no glazing",
        "no glass",
        "not glazed",
        "unglazed",
        "sans vitrage",
        "sans verre",
        "non vitree",
        "non-vitree",
        "opaque",
        "solid",
        "unknown",
        "inconnu",
        "indetermine",
    )
    if any(token in value for token in negative):
        return False

    # This field describes glazing rather than generic opening appearance. Once
    # it contains a non-negative observed descriptor (e.g. clear, glass,
    # translucent, double), the presence of glazing itself is established even
    # if the descriptor does not literally contain the word "glass".
    return True


def _is_glazed_door(opening: SceneOpening) -> bool:
    if opening.type is not OpeningType.DOOR:
        return False

    structured = _structured_glazing_state(opening)
    if structured is not None:
        return structured

    text = _opening_text(opening)
    # Legacy fallback for scenes created before structured opening composition.
    # Negative evidence wins because a phrase such as "non vitrée" still
    # contains the substring "vitrée".
    if any(token in text for token in ("non vitree", "non-vitree", "sans vitrage", "not glazed", "unglazed")):
        return False
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
    opening_id: str,
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
        opening_id=opening_id,
    )


def _opening_grid(opening: SceneOpening, scene: ArchitecturalScene, *, origin_x: float, origin_y: float, origin_z: float, studs_per_meter: float) -> tuple[int, int, int, int, int, int, int, int]:
    """Rasterize one opening relative to its own SceneVolume and global Scene origin."""
    volume = next(item for item in scene.volumes if item.id == opening.volume_id)
    courses_per_meter = studs_per_meter * COURSES_PER_STUD_RATIO
    volume_x = _round_half_up((volume.position.x - origin_x) * studs_per_meter)
    volume_y = _round_half_up((volume.position.y - origin_y) * studs_per_meter)
    volume_width = max(1, _round_half_up(volume.width.value * studs_per_meter))
    volume_depth = max(1, _round_half_up(volume.depth.value * studs_per_meter))
    local = max(0, _round_half_up(opening.offset_horizontal * studs_per_meter))
    z0 = max(0, _round_half_up((volume.position.z + opening.offset_vertical - origin_z) * courses_per_meter))
    width = max(1, _round_half_up(opening.width * studs_per_meter))
    height = max(1, _round_half_up(opening.height * courses_per_meter))
    return volume_x, volume_y, volume_width, volume_depth, local, z0, width, height


def _global_cell(facade: Facade, *, house_x: int, house_y: int, house_width: int, house_depth: int, local_x: int, z_course: int) -> tuple[int, int, int, int]:
    z = z_course * 3
    if facade is Facade.FRONT:
        return house_x + local_x, house_y, z, 1
    if facade is Facade.REAR:
        return house_x + house_width - local_x - 1, house_y + house_depth - 1, z, 1
    if facade is Facade.RIGHT:
        return house_x + house_width - 1, house_y + local_x, z, 0
    return house_x, house_y + house_depth - local_x - 1, z, 0


def _opening_parts(opening: SceneOpening, scene: ArchitecturalScene, *, origin_x: float, origin_y: float, origin_z: float, studs_per_meter: float) -> list[BrickModelPart]:
    glass_blocks = _is_glass_block(opening)
    glazed_door = _is_glazed_door(opening)
    if not glass_blocks and not glazed_door:
        return []
    house_x, house_y, house_width, house_depth, local, z0, width, height = _opening_grid(opening, scene, origin_x=origin_x, origin_y=origin_y, origin_z=origin_z, studs_per_meter=studs_per_meter)
    parts: list[BrickModelPart] = []
    index = 1
    for dx in range(width):
        for dz in range(height):
            # Explicit glazing proves glazing, not the exact thickness/layout of
            # a surrounding frame. Until Scene has explicit door-frame geometry,
            # render only glazing cells rather than inventing a perimeter frame.
            category = "window_pane"
            gx, gy, gz, rotation = _global_cell(opening.facade, house_x=house_x, house_y=house_y, house_width=house_width, house_depth=house_depth, local_x=local + dx, z_course=z0 + dz)
            parts.append(
                _part(
                    f"scene-glazing:{opening.id}:{index:05d}",
                    x=gx,
                    y=gy,
                    z=gz,
                    facade=opening.facade,
                    category=category,
                    rotation=rotation,
                    opening_id=opening.id,
                )
            )
            index += 1
    return parts


def augment_brick_model_with_scene_glazing(model: BrickModel, scene: ArchitecturalScene, *, front_width_studs: int) -> BrickModel:
    """Apply final Scene details without inventing unsupported geometry."""
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")

    # Chimneys are independent of glazing but belong to the same final
    # Scene-aware detail pass in the current M0 orchestration. Their renderer uses
    # only explicit metric Scene geometry and never infers roof shape or caps.
    model = augment_brick_model_with_scene_chimneys(
        model,
        scene,
        front_width_studs=front_width_studs,
    )

    targets = [opening for opening in scene.openings if _is_glass_block(opening) or _is_glazed_door(opening)]
    if targets:
        main = scene.volumes[0]
        studs_per_meter = front_width_studs / main.width.value
        origin_x, origin_y, origin_z = _scene_bounds(scene)
        extra: list[BrickModelPart] = []
        for opening in targets:
            extra.extend(_opening_parts(opening, scene, origin_x=origin_x, origin_y=origin_y, origin_z=origin_z, studs_per_meter=studs_per_meter))
        if extra:
            target_cells = {(part.x_studs, part.y_studs, part.z_plates, part.facade) for part in extra}
            replaceable_categories = {"brick", "facade_detail", "window_frame", "window_pane"}
            kept = [
                part for part in model.parts
                if not (
                    part.component == "facade_detail"
                    and part.category in replaceable_categories
                    and (part.x_studs, part.y_studs, part.z_plates, part.facade) in target_cells
                )
            ]
            model = model.model_copy(update={"parts": [*kept, *extra]})

    # Wall thickness/reveal observations are applied last so every glazing path,
    # including Scene-only glass blocks and glazed doors, moves to the same
    # evidence-backed recessed plane. Unknown or low-confidence metric depth is
    # intentionally ignored by the wall-depth projector.
    return augment_brick_model_with_wall_depth(
        model,
        scene,
        front_width_studs=front_width_studs,
    )
