"""Render metric ArchitecturalScene chimneys as conservative LEGO prisms."""
from __future__ import annotations

from math import ceil

from brickhouse.scene.models import ArchitecturalScene

from .brick_model import BrickModel, BrickModelPart
from .roof import create_m0_roof_catalog
from .scaling import COURSES_PER_STUD_RATIO
from .scene_architecture import (
    EPSILON,
    _brick,
    _course_z,
    _nearest_facade,
    _round_half_up,
    _scene_bounds,
)


def _roof_footprint(part: BrickModelPart) -> set[tuple[int, int]]:
    """Return the conservative stud footprint of a canonical roof placement."""
    definition = create_m0_roof_catalog().get(part.part_id)
    footprint_x, footprint_y = (
        (definition.length_studs, definition.width_studs)
        if part.rotation_quarter_turns % 2
        else (definition.width_studs, definition.length_studs)
    )
    return {
        (part.x_studs + dx, part.y_studs + dy)
        for dx in range(footprint_x)
        for dy in range(footprint_y)
    }


def _roof_intersects_chimney(
    part: BrickModelPart,
    chimney_cells: set[tuple[int, int]],
    chimney_z0: int,
    chimney_z1: int,
) -> bool:
    if part.component != "roof":
        return False
    definition = create_m0_roof_catalog().get(part.part_id)
    roof_z0 = part.z_plates
    roof_z1 = roof_z0 + definition.height_plates
    vertical_overlap = roof_z0 < chimney_z1 and chimney_z0 < roof_z1
    return vertical_overlap and bool(_roof_footprint(part).intersection(chimney_cells))


def augment_brick_model_with_scene_chimneys(
    model: BrickModel,
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> BrickModel:
    """Add only the rectangular chimney geometry explicitly present in Scene.

    The renderer deliberately does not infer caps, flues, material, roof pitch, or
    hidden penetration geometry. When an explicit metric chimney crosses an
    already-rendered roof element, that whole roof element is removed to create a
    conservative physical opening rather than allowing two LEGO solids to occupy
    the same space. ArchitecturalScene dimensions remain authoritative.
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

    chimney_specs = []
    for chimney in scene.chimneys:
        x0 = _round_half_up((chimney.position.x - origin_x) * studs_per_meter)
        y0 = _round_half_up((chimney.position.y - origin_y) * studs_per_meter)
        z0 = _course_z(chimney.position.z, origin_z, plates_per_meter)
        width = max(1, ceil(chimney.width * studs_per_meter - EPSILON))
        depth = max(1, ceil(chimney.depth * studs_per_meter - EPSILON))
        courses = max(1, ceil(chimney.height * plates_per_meter / 3.0 - EPSILON))
        cells = {
            (x0 + dx, y0 + dy)
            for dx in range(width)
            for dy in range(depth)
        }
        chimney_specs.append((chimney, x0, y0, z0, width, depth, courses, cells))

    # A roof part is an indivisible physical LEGO element. If any part of its
    # conservative footprint crosses a metric chimney prism, remove the full
    # element instead of pretending that the chimney can pass through it.
    retained_parts = []
    for part in model.parts:
        if any(
            _roof_intersects_chimney(part, cells, z0, z0 + courses * 3)
            for _, _, _, z0, _, _, courses, cells in chimney_specs
        ):
            continue
        retained_parts.append(part)

    occupied = {(part.x_studs, part.y_studs, part.z_plates) for part in retained_parts}
    extra = []

    for chimney, x0, y0, z0, width, depth, courses, _ in chimney_specs:
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

    parts = [*retained_parts, *extra]
    if parts == model.parts:
        return model
    return model.model_copy(
        update={
            "width_studs": max(model.width_studs, max(part.x_studs + 1 for part in parts)),
            "depth_studs": max(model.depth_studs, max(part.y_studs + 1 for part in parts)),
            "height_plates": max(model.height_plates, max(part.z_plates + 3 for part in parts)),
            "parts": parts,
        }
    )
