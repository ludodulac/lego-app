"""Render metric ArchitecturalScene chimneys as conservative LEGO prisms."""
from __future__ import annotations

from math import ceil

from brickhouse.scene.models import ArchitecturalScene

from .brick_model import BrickModel
from .scaling import COURSES_PER_STUD_RATIO
from .scene_architecture import (
    EPSILON,
    _brick,
    _course_z,
    _nearest_facade,
    _round_half_up,
    _scene_bounds,
)


def augment_brick_model_with_scene_chimneys(
    model: BrickModel,
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> BrickModel:
    """Add only the rectangular chimney geometry explicitly present in Scene.

    The renderer deliberately does not infer caps, flues, material, roof pitch, or
    hidden penetration geometry. Existing occupied LEGO cells win, so a chimney
    may emerge through an already-rendered roof without duplicating placements.
    """
    if not scene.chimneys:
        return model
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")

    main = scene.volumes[0]
    if main.width.value is None:
        return model
    studs_per_meter = front_width_studs / main.width.value
    plates_per_meter = studs_per_meter * COURSES_PER_STUD_RATIO * 3
    origin_x, origin_y, origin_z = _scene_bounds(scene)

    occupied = {(part.x_studs, part.y_studs, part.z_plates) for part in model.parts}
    extra = []

    for chimney in scene.chimneys:
        x0 = _round_half_up((chimney.position.x - origin_x) * studs_per_meter)
        y0 = _round_half_up((chimney.position.y - origin_y) * studs_per_meter)
        z0 = _course_z(chimney.position.z, origin_z, plates_per_meter)
        width = max(1, ceil(chimney.width * studs_per_meter - EPSILON))
        depth = max(1, ceil(chimney.depth * studs_per_meter - EPSILON))
        courses = max(1, ceil(chimney.height * plates_per_meter / 3.0 - EPSILON))
        facade = _nearest_facade(
            scene,
            chimney.position.x + chimney.width / 2,
            chimney.position.y + chimney.depth / 2,
        )
        index = 1
        for course in range(courses):
            z = z0 + course * 3
            for dx in range(width):
                for dy in range(depth):
                    key = (x0 + dx, y0 + dy, z)
                    if key in occupied:
                        continue
                    occupied.add(key)
                    extra.append(
                        _brick(
                            f"scene-chimney:{chimney.id}:{index:05d}",
                            key[0],
                            key[1],
                            key[2],
                            facade,
                        )
                    )
                    index += 1

    if not extra:
        return model
    parts = [*model.parts, *extra]
    return model.model_copy(
        update={
            "width_studs": max(model.width_studs, max(part.x_studs + 1 for part in parts)),
            "depth_studs": max(model.depth_studs, max(part.y_studs + 1 for part in parts)),
            "height_plates": max(model.height_plates, max(part.z_plates + 3 for part in parts)),
            "parts": parts,
        }
    )
