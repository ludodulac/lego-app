"""Add rich ArchitecturalScene exterior elements to an already-built BrickModel.

This is intentionally a small M0 bridge: platforms and straight stair runs are
represented with canonical 1x1 bricks so their location and massing survive into
the viewer/BOM/assembly pipeline. Fidelity can improve later without losing the
architectural constraints carried by the Scene.
"""
from __future__ import annotations

from math import ceil

from brickhouse.building.models import Facade
from brickhouse.scene.models import ArchitecturalScene, Platform, StairRun

from .brick_model import BrickModel, BrickModelPart
from .scaling import COURSES_PER_STUD_RATIO


def _round_half_up(value: float) -> int:
    return int(value + 0.5)


def _scene_bounds(scene: ArchitecturalScene) -> tuple[float, float, float]:
    xs = [volume.position.x for volume in scene.volumes]
    ys = [volume.position.y for volume in scene.volumes]
    zs = [volume.position.z for volume in scene.volumes]
    for platform in scene.platforms:
        xs.append(platform.position.x)
        ys.append(platform.position.y)
        zs.append(0.0)
    for stair in scene.stairs:
        xs.extend([stair.start.x, stair.end.x])
        ys.extend([stair.start.y, stair.end.y])
        zs.extend([stair.start.z, stair.end.z])
    return min(xs), min(ys), min(zs)


def _volume_bounds(scene: ArchitecturalScene) -> tuple[float, float, float]:
    return (
        min(volume.position.x for volume in scene.volumes),
        min(volume.position.y for volume in scene.volumes),
        min(volume.position.z for volume in scene.volumes),
    )


def _nearest_facade(scene: ArchitecturalScene, x: float, y: float) -> Facade:
    main = scene.volumes[0]
    left = main.position.x
    right = left + main.width.value
    front = main.position.y
    rear = front + main.depth.value
    distances = [
        (abs(x - left), Facade.LEFT),
        (abs(x - right), Facade.RIGHT),
        (abs(y - front), Facade.FRONT),
        (abs(y - rear), Facade.REAR),
    ]
    return min(distances, key=lambda item: item[0])[1]


def _brick(
    placement_id: str,
    x: int,
    y: int,
    z: int,
    facade: Facade,
) -> BrickModelPart:
    return BrickModelPart(
        placement_id=placement_id,
        part_id="BRICK_1X1",
        category="brick",
        component="facade_detail",
        x_studs=x,
        y_studs=y,
        z_plates=z,
        rotation_quarter_turns=0,
        facade=facade,
    )


def _platform_parts(
    platform: Platform,
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    origin_z: float,
    studs_per_meter: float,
    plates_per_meter: float,
) -> list[BrickModelPart]:
    x0 = _round_half_up((platform.position.x - origin_x) * studs_per_meter)
    y0 = _round_half_up((platform.position.y - origin_y) * studs_per_meter)
    z0 = max(0, _round_half_up((platform.position.z - origin_z) * plates_per_meter))
    width = max(1, _round_half_up(platform.width * studs_per_meter))
    depth = max(1, _round_half_up(platform.depth * studs_per_meter))
    courses = max(1, ceil(platform.thickness * plates_per_meter / 3.0))
    facade = _nearest_facade(scene, platform.position.x + platform.width / 2, platform.position.y + platform.depth / 2)

    parts: list[BrickModelPart] = []
    index = 1
    for course in range(courses):
        z = z0 + course * 3
        for dx in range(width):
            for dy in range(depth):
                parts.append(_brick(f"scene-platform:{platform.id}:{index:05d}", x0 + dx, y0 + dy, z, facade))
                index += 1

    # If the Scene does not yet contain explicit post geometry, add four simple
    # support posts as a conservative structural default. They are deliberately
    # subordinate to the deck and can later be replaced by richer timber parts.
    post_cells = {(x0, y0), (x0 + width - 1, y0), (x0, y0 + depth - 1), (x0 + width - 1, y0 + depth - 1)}
    for post_index, (x, y) in enumerate(sorted(post_cells), start=1):
        z = 0
        while z < z0:
            parts.append(_brick(f"scene-platform:{platform.id}:post{post_index}:{z:04d}", x, y, z, facade))
            z += 3
    return parts


def _stair_parts(
    stair: StairRun,
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    origin_z: float,
    studs_per_meter: float,
    plates_per_meter: float,
) -> list[BrickModelPart]:
    sx = _round_half_up((stair.start.x - origin_x) * studs_per_meter)
    sy = _round_half_up((stair.start.y - origin_y) * studs_per_meter)
    sz = max(0, _round_half_up((stair.start.z - origin_z) * plates_per_meter))
    ex = _round_half_up((stair.end.x - origin_x) * studs_per_meter)
    ey = _round_half_up((stair.end.y - origin_y) * studs_per_meter)
    ez = max(0, _round_half_up((stair.end.z - origin_z) * plates_per_meter))
    dx, dy = ex - sx, ey - sy
    steps = max(abs(dx), abs(dy), 1)
    width = max(1, _round_half_up(stair.width * studs_per_meter))
    facade = _nearest_facade(scene, (stair.start.x + stair.end.x) / 2, (stair.start.y + stair.end.y) / 2)
    along_x = abs(dx) >= abs(dy)

    parts: list[BrickModelPart] = []
    seen: set[tuple[int, int, int]] = set()
    index = 1
    for step in range(steps + 1):
        t = step / steps
        x = _round_half_up(sx + dx * t)
        y = _round_half_up(sy + dy * t)
        # LEGO vertical geometry lives on brick courses; this keeps each tread
        # visibly supported rather than producing fractional floating plates.
        z = max(0, 3 * _round_half_up((sz + (ez - sz) * t) / 3.0))
        for offset in range(width):
            px = x if along_x else x + offset
            py = y + offset if along_x else y
            key = (px, py, z)
            if key in seen:
                continue
            seen.add(key)
            parts.append(_brick(f"scene-stair:{stair.id}:{index:05d}", px, py, z, facade))
            index += 1
    return parts


def augment_brick_model_with_scene_architecture(
    model: BrickModel,
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> BrickModel:
    """Return a BrickModel that also contains Scene platforms and stairs."""
    if not scene.platforms and not scene.stairs:
        return model
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")

    main = scene.volumes[0]
    studs_per_meter = front_width_studs / main.width.value
    plates_per_meter = studs_per_meter * COURSES_PER_STUD_RATIO * 3
    origin_x, origin_y, origin_z = _scene_bounds(scene)
    volume_x, volume_y, volume_z = _volume_bounds(scene)
    shift_x = _round_half_up((volume_x - origin_x) * studs_per_meter)
    shift_y = _round_half_up((volume_y - origin_y) * studs_per_meter)
    shift_z = max(0, _round_half_up((volume_z - origin_z) * plates_per_meter))

    shifted = [
        part.model_copy(update={
            "x_studs": part.x_studs + shift_x,
            "y_studs": part.y_studs + shift_y,
            "z_plates": part.z_plates + shift_z,
        })
        for part in model.parts
    ]
    extra: list[BrickModelPart] = []
    for platform in scene.platforms:
        extra.extend(_platform_parts(
            platform, scene,
            origin_x=origin_x, origin_y=origin_y, origin_z=origin_z,
            studs_per_meter=studs_per_meter, plates_per_meter=plates_per_meter,
        ))
    for stair in scene.stairs:
        extra.extend(_stair_parts(
            stair, scene,
            origin_x=origin_x, origin_y=origin_y, origin_z=origin_z,
            studs_per_meter=studs_per_meter, plates_per_meter=plates_per_meter,
        ))

    all_parts = shifted + extra
    width = max(model.width_studs + shift_x, max(part.x_studs + 1 for part in all_parts))
    depth = max(model.depth_studs + shift_y, max(part.y_studs + 1 for part in all_parts))
    height = max(model.height_plates + shift_z, max(part.z_plates + 3 for part in all_parts))
    return model.model_copy(update={"width_studs": width, "depth_studs": depth, "height_plates": height, "parts": all_parts})
