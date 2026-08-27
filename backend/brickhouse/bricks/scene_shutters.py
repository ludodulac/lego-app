"""Evidence-gated Scene shutter augmentation.

Shutter mechanism/style does not prove pose. This module therefore renders only
one canonical pose whose geometry fits the current facade plane without inventing
an unsupported outward depth: ``open_folded_at_sides``.
"""
from __future__ import annotations

import unicodedata

from brickhouse.building.models import Facade, OpeningType
from brickhouse.scene import ArchitecturalScene
from brickhouse.scene.models import SceneOpening

from .brick_model import BrickModel, BrickModelPart, EXTERIOR_MATERIAL_CATEGORIES
from .scene_architecture import _scene_bounds
from .scene_glazing import _global_cell, _opening_grid

_OPEN_FOLDED_STATE = "open_folded_at_sides"


def _normalized(value: str | None) -> str | None:
    if value is None:
        return None
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return "_".join(text.strip().lower().replace("-", "_").split())


def _renderable_open_shutters(opening: SceneOpening) -> bool:
    visual = opening.opening_visual
    if opening.type is not OpeningType.WINDOW or visual is None:
        return False
    # Count and style establish that the observed objects are a paired folding
    # shutter assembly. Pose remains an independent fact and must match the
    # canonical state exactly; prose such as "open" is intentionally not enough.
    style = _normalized(visual.shutter_style)
    return (
        visual.shutter_count == 2
        and style is not None
        and "fold" in style
        and _normalized(visual.shutter_state) == _OPEN_FOLDED_STATE
    )


def _shutter_parts(
    opening: SceneOpening,
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    origin_z: float,
    studs_per_meter: float,
) -> list[BrickModelPart]:
    house_x, house_y, house_width, house_depth, local, z0, width, height = _opening_grid(
        opening,
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        origin_z=origin_z,
        studs_per_meter=studs_per_meter,
    )
    wall_width = house_width if opening.facade in {Facade.FRONT, Facade.REAR} else house_depth
    # A folded shutter is represented by one vertical 1-stud strip beside each
    # jamb. This is deliberately simple, placement-approved, and outside the
    # opening void. If an opening touches a wall edge, that side is omitted rather
    # than pushed onto a neighboring facade.
    shutter_columns = []
    left = local - 1
    right = local + width
    if 0 <= left < wall_width:
        shutter_columns.append(("left", left))
    if 0 <= right < wall_width:
        shutter_columns.append(("right", right))

    semantic_color = opening.opening_visual.shutter_color if opening.opening_visual else None
    parts: list[BrickModelPart] = []
    for side, local_x in shutter_columns:
        for dz in range(height):
            gx, gy, gz, rotation = _global_cell(
                opening.facade,
                house_x=house_x,
                house_y=house_y,
                house_width=house_width,
                house_depth=house_depth,
                local_x=local_x,
                z_course=z0 + dz,
            )
            parts.append(
                BrickModelPart(
                    placement_id=f"scene-shutter:{opening.id}:{side}:{dz + 1:03d}",
                    part_id="BRICK_1X1",
                    category="facade_detail",
                    component="facade_detail",
                    x_studs=gx,
                    y_studs=gy,
                    z_plates=gz,
                    rotation_quarter_turns=rotation,
                    facade=opening.facade,
                    opening_id=opening.id,
                    semantic_color=semantic_color,
                )
            )
    return parts


def augment_brick_model_with_scene_shutters(
    model: BrickModel,
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> BrickModel:
    """Add shutters only when an explicit canonical observed pose is available."""
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")
    targets = [opening for opening in scene.openings if _renderable_open_shutters(opening)]
    if not targets:
        return model

    main = scene.volumes[0]
    if main.width.value is None:
        return model
    studs_per_meter = front_width_studs / main.width.value
    origin_x, origin_y, origin_z = _scene_bounds(scene)
    extra: list[BrickModelPart] = []
    for opening in targets:
        extra.extend(
            _shutter_parts(
                opening,
                scene,
                origin_x=origin_x,
                origin_y=origin_y,
                origin_z=origin_z,
                studs_per_meter=studs_per_meter,
            )
        )
    if not extra:
        return model

    # A folded shutter sits on top of the surround/wall face beside the opening.
    # When semantic surround detail already owns that exact facade-detail cell,
    # the shutter becomes the visible exterior detail there. Glazing and wall
    # structure are never removed.
    target_cells = {(p.x_studs, p.y_studs, p.z_plates, p.facade) for p in extra}
    replaceable_detail_categories = {"facade_detail", *EXTERIOR_MATERIAL_CATEGORIES}
    kept = [
        part
        for part in model.parts
        if not (
            part.component == "facade_detail"
            and part.category in replaceable_detail_categories
            and part.opening_id is not None
            and (part.x_studs, part.y_studs, part.z_plates, part.facade) in target_cells
        )
    ]
    return model.model_copy(update={"parts": [*kept, *extra]})
