"""Add rich ArchitecturalScene exterior elements to an already-built BrickModel.

M0 bridge for exterior architecture. Platforms and stair runs are reconstructed
from the validated Scene instead of being flattened away by BuildingModel 0.1.
The current Scene schema does not yet expose a dedicated material field, so this
module reads conservative material hints from object ids/evidence/notes. Geometry
remains subordinate to Scene coordinates: hints may change representation, never
position, orientation or adjacency.
"""
from __future__ import annotations

from math import ceil
import unicodedata

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


def _normalized_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(text.split())


def _object_text(obj, scene: ArchitecturalScene) -> str:
    evidence = " ".join(item.observation for item in getattr(obj, "evidence", []))
    return _normalized_text(f"{obj.id} {evidence} {scene.notes or ''}")


def _is_timber(obj, scene: ArchitecturalScene) -> bool:
    text = _object_text(obj, scene)
    return any(token in text for token in ("bois", "timber", "wood", "lattes", "garde-corps bois"))


def _is_masonry(obj, scene: ArchitecturalScene) -> bool:
    text = _object_text(obj, scene)
    return any(token in text for token in ("beton", "concrete", "maconne", "masonry", "pierre", "muret", "enduit"))


def _brick(
    placement_id: str,
    x: int,
    y: int,
    z: int,
    facade: Facade,
    *,
    part_id: str = "BRICK_1X1",
    category: str = "brick",
) -> BrickModelPart:
    return BrickModelPart(
        placement_id=placement_id,
        part_id=part_id,
        category=category,
        component="facade_detail",
        x_studs=max(0, x),
        y_studs=max(0, y),
        z_plates=max(0, z),
        rotation_quarter_turns=0,
        facade=facade,
    )


def _add_vertical_column(parts: list[BrickModelPart], *, prefix: str, x: int, y: int, z_from: int, z_to: int, facade: Facade, index_start: int) -> int:
    index = index_start
    z = max(0, z_from)
    while z <= z_to:
        parts.append(_brick(f"{prefix}:{index:05d}", x, y, z, facade))
        index += 1
        z += 3
    return index


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
    facade = _nearest_facade(scene, platform.position.x + platform.width / 2, platform.position.y + platform.depth / 2)
    timber = _is_timber(platform, scene)
    masonry = _is_masonry(platform, scene) and not timber

    parts: list[BrickModelPart] = []
    index = 1

    # Timber terraces are decks, not solid cuboids. Keep only a thin structural
    # deck at the Scene elevation. Masonry landings retain their full thickness.
    courses = 1 if timber else max(1, ceil(platform.thickness * plates_per_meter / 3.0))
    for course in range(courses):
        z = z0 + course * 3
        for dx in range(width):
            for dy in range(depth):
                parts.append(_brick(f"scene-platform:{platform.id}:deck:{index:05d}", x0 + dx, y0 + dy, z, facade))
                index += 1

    # Prefer explicit supports. If the Scene has not yet measured them, a timber
    # deck gets a sparse support grid rather than the previous four arbitrary
    # corner posts. Masonry landings do not receive invented timber posts.
    support_cells: set[tuple[int, int]] = set()
    if platform.supports:
        for support in platform.supports:
            support_cells.add((
                _round_half_up((support.position.x - origin_x) * studs_per_meter),
                _round_half_up((support.position.y - origin_y) * studs_per_meter),
            ))
    elif timber:
        xs = {x0, x0 + width - 1}
        if width >= 8:
            xs.add(x0 + width // 2)
        ys = {y0, y0 + depth - 1}
        if depth >= 10:
            ys.add(y0 + depth // 2)
        support_cells = {(x, y) for x in xs for y in ys}

    for post_index, (x, y) in enumerate(sorted(support_cells), start=1):
        z = 0
        while z < z0:
            parts.append(_brick(f"scene-platform:{platform.id}:support{post_index}:{z:04d}", x, y, z, facade))
            z += 3

    # If the evidence explicitly describes a solid masonry parapet/muret, retain
    # a low perimeter wall. Do not invent it for timber decks.
    if masonry and any(token in _object_text(platform, scene) for token in ("muret", "parapet", "garde-corps plein")):
        rail_top = z0 + 6
        perimeter = {(x0 + dx, y0) for dx in range(width)} | {(x0 + dx, y0 + depth - 1) for dx in range(width)}
        perimeter |= {(x0, y0 + dy) for dy in range(depth)} | {(x0 + width - 1, y0 + dy) for dy in range(depth)}
        for x, y in sorted(perimeter):
            index = _add_vertical_column(parts, prefix=f"scene-platform:{platform.id}:parapet", x=x, y=y, z_from=z0 + 3, z_to=rail_top, facade=facade, index_start=index)

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
    masonry = _is_masonry(stair, scene)

    parts: list[BrickModelPart] = []
    seen: set[tuple[int, int, int]] = set()
    index = 1
    for step in range(steps + 1):
        t = step / steps
        x = _round_half_up(sx + dx * t)
        y = _round_half_up(sy + dy * t)
        z = max(0, 3 * _round_half_up((sz + (ez - sz) * t) / 3.0))

        tread_cells: list[tuple[int, int]] = []
        for offset in range(width):
            px = x if along_x else x + offset
            py = y + offset if along_x else y
            tread_cells.append((px, py))
            key = (px, py, z)
            if key in seen:
                continue
            seen.add(key)
            parts.append(_brick(f"scene-stair:{stair.id}:tread:{index:05d}", px, py, z, facade))
            index += 1

        if masonry:
            # A rendered concrete/stone stair is a supported mass, not floating
            # treads. Fill below each tread and extend the two side cells above
            # the tread to create the observed solid ramp/muret silhouette.
            for px, py in tread_cells:
                fill_z = 0
                while fill_z < z:
                    key = (px, py, fill_z)
                    if key not in seen:
                        seen.add(key)
                        parts.append(_brick(f"scene-stair:{stair.id}:body:{index:05d}", px, py, fill_z, facade))
                        index += 1
                    fill_z += 3
            if tread_cells:
                side_cells = {tread_cells[0], tread_cells[-1]}
                for px, py in side_cells:
                    for wall_z in (z + 3, z + 6):
                        key = (px, py, wall_z)
                        if key in seen:
                            continue
                        seen.add(key)
                        parts.append(_brick(f"scene-stair:{stair.id}:sidewall:{index:05d}", px, py, wall_z, facade))
                        index += 1

    return parts


def augment_brick_model_with_scene_architecture(
    model: BrickModel,
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> BrickModel:
    """Return a BrickModel that also contains all Scene platforms and stair runs."""
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