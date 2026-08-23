"""Add rich ArchitecturalScene exterior elements to an already-built BrickModel.

M0 bridge for exterior architecture. Platforms, stair runs and facade grade
profiles are reconstructed from the validated Scene instead of being flattened
away by BuildingModel 0.1. New scenes carry structured material/edge metadata;
legacy text hints remain only as a backwards-compatible fallback.
"""
from __future__ import annotations

from math import ceil
import unicodedata

from brickhouse.building.models import Facade
from brickhouse.scene.models import (
    ArchitecturalScene,
    EdgeTreatment,
    ExteriorMaterial,
    Platform,
    StairRun,
)

from .brick_model import BrickModel, BrickModelPart
from .scaling import COURSES_PER_STUD_RATIO


EPSILON = 1e-6


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

    if scene.terrain and scene.terrain.profiles:
        main = scene.volumes[0]
        facades = {profile.facade for profile in scene.terrain.profiles}
        if Facade.LEFT in facades:
            xs.append(main.position.x - 0.5)
        if Facade.RIGHT in facades:
            xs.append(main.position.x + main.width.value + 0.5)
        if Facade.FRONT in facades:
            ys.append(main.position.y - 0.5)
        if Facade.REAR in facades:
            ys.append(main.position.y + main.depth.value + 0.5)
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
    if getattr(obj, "material", None) is not None:
        return obj.material is ExteriorMaterial.TIMBER
    text = _object_text(obj, scene)
    return any(token in text for token in ("bois", "timber", "wood", "lattes", "garde-corps bois"))


def _is_masonry(obj, scene: ArchitecturalScene) -> bool:
    material = getattr(obj, "material", None)
    if material is not None:
        return material in {ExteriorMaterial.CONCRETE, ExteriorMaterial.MASONRY, ExteriorMaterial.STONE}
    text = _object_text(obj, scene)
    return any(token in text for token in ("beton", "concrete", "maconne", "masonry", "pierre", "muret", "enduit"))


def _platform_has_solid_parapet(platform: Platform, scene: ArchitecturalScene) -> bool:
    if platform.edge_treatment is not None:
        return platform.edge_treatment is EdgeTreatment.SOLID_PARAPET
    return any(token in _object_text(platform, scene) for token in ("muret", "parapet", "garde-corps plein"))


def _stair_solid_edges(stair: StairRun, scene: ArchitecturalScene) -> tuple[bool, bool]:
    if stair.left_edge is not None or stair.right_edge is not None:
        return (
            stair.left_edge is EdgeTreatment.SOLID_PARAPET,
            stair.right_edge is EdgeTreatment.SOLID_PARAPET,
        )
    legacy_solid = _is_masonry(stair, scene) and any(
        token in _object_text(stair, scene) for token in ("muret", "parapet", "rampe beton", "rampe en beton")
    )
    return legacy_solid, legacy_solid


def _validate_exterior_primitives(scene: ArchitecturalScene) -> None:
    """Reject generic exterior shapes that silently wrap or cut through a house."""
    main = scene.volumes[0]
    left = main.position.x
    right = left + main.width.value
    front = main.position.y
    rear = front + main.depth.value

    for platform in scene.platforms:
        x0 = platform.position.x
        x1 = x0 + platform.width
        y0 = platform.position.y
        y1 = y0 + platform.depth
        sides = []
        if x1 <= left + EPSILON:
            sides.append(Facade.LEFT)
        if x0 >= right - EPSILON:
            sides.append(Facade.RIGHT)
        if y1 <= front + EPSILON:
            sides.append(Facade.FRONT)
        if y0 >= rear - EPSILON:
            sides.append(Facade.REAR)
        if not sides:
            raise ValueError(
                f"platform {platform.id!r} intersects the main building footprint; "
                "split attached exterior structures into primitives outside one facade"
            )
        if len(sides) > 1:
            raise ValueError(
                f"platform {platform.id!r} wraps a building corner; split it into one Platform per rectilinear facade segment"
            )
        side = sides[0]
        if side in {Facade.LEFT, Facade.RIGHT} and (y0 < front - EPSILON or y1 > rear + EPSILON):
            raise ValueError(f"platform {platform.id!r} extends past a side-facade corner; split the geometry")
        if side in {Facade.FRONT, Facade.REAR} and (x0 < left - EPSILON or x1 > right + EPSILON):
            raise ValueError(f"platform {platform.id!r} extends past a front/rear corner; split the geometry")

    for stair in scene.stairs:
        dx = abs(stair.end.x - stair.start.x)
        dy = abs(stair.end.y - stair.start.y)
        if dx > EPSILON and dy > EPSILON:
            raise ValueError(
                f"stair {stair.id!r} changes two horizontal axes in one run; "
                "split turning stairs into axis-aligned StairRun objects joined by a landing"
            )


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


def _add_vertical_column(
    parts: list[BrickModelPart], *, prefix: str, x: int, y: int,
    z_from: int, z_to: int, facade: Facade, index_start: int,
) -> int:
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
    courses = 1 if timber else max(1, ceil(platform.thickness * plates_per_meter / 3.0))
    for course in range(courses):
        z = z0 + course * 3
        for dx in range(width):
            for dy in range(depth):
                parts.append(_brick(f"scene-platform:{platform.id}:deck:{index:05d}", x0 + dx, y0 + dy, z, facade))
                index += 1

    support_cells: set[tuple[int, int]] = set()
    for support in platform.supports:
        support_cells.add((
            _round_half_up((support.position.x - origin_x) * studs_per_meter),
            _round_half_up((support.position.y - origin_y) * studs_per_meter),
        ))

    for post_index, (x, y) in enumerate(sorted(support_cells), start=1):
        z = 0
        while z < z0:
            parts.append(_brick(f"scene-platform:{platform.id}:support{post_index}:{z:04d}", x, y, z, facade))
            z += 3

    if masonry and _platform_has_solid_parapet(platform, scene):
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
    left_solid, right_solid = _stair_solid_edges(stair, scene)

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
            edge_cells: list[tuple[int, int]] = []
            if left_solid:
                edge_cells.append(tread_cells[0])
            if right_solid and (not left_solid or tread_cells[-1] != tread_cells[0]):
                edge_cells.append(tread_cells[-1])
            for px, py in edge_cells:
                for wall_z in (z + 3, z + 6):
                    key = (px, py, wall_z)
                    if key in seen:
                        continue
                    seen.add(key)
                    parts.append(_brick(f"scene-stair:{stair.id}:sidewall:{index:05d}", px, py, wall_z, facade))
                    index += 1

    return parts


def _terrain_parts(
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    origin_z: float,
    studs_per_meter: float,
    plates_per_meter: float,
) -> list[BrickModelPart]:
    """Render grade profiles as a stepped ground surface, not a retaining wall."""
    if not scene.terrain or not scene.terrain.profiles:
        return []

    main = scene.volumes[0]
    x0 = _round_half_up((main.position.x - origin_x) * studs_per_meter)
    y0 = _round_half_up((main.position.y - origin_y) * studs_per_meter)
    width = max(1, _round_half_up(main.width.value * studs_per_meter))
    depth = max(1, _round_half_up(main.depth.value * studs_per_meter))
    band = max(1, _round_half_up(0.4 * studs_per_meter))
    parts: list[BrickModelPart] = []
    index = 1

    for profile in scene.terrain.profiles:
        length = width if profile.facade in {Facade.FRONT, Facade.REAR} else depth
        if length <= 0:
            continue
        start_z = max(0, _round_half_up((profile.start_elevation - origin_z) * plates_per_meter))
        end_z = max(0, _round_half_up((profile.end_elevation - origin_z) * plates_per_meter))

        for along in range(length):
            t = along / max(length - 1, 1)
            grade_z = max(0, 3 * _round_half_up((start_z + (end_z - start_z) * t) / 3.0))
            for across in range(band):
                if profile.facade is Facade.RIGHT:
                    px, py = x0 + width + across, y0 + along
                elif profile.facade is Facade.LEFT:
                    px, py = x0 - 1 - across, y0 + depth - 1 - along
                elif profile.facade is Facade.FRONT:
                    px, py = x0 + along, y0 - 1 - across
                else:
                    px, py = x0 + width - 1 - along, y0 + depth + across
                parts.append(_brick(
                    f"scene-terrain:{profile.facade.value}:{index:06d}",
                    px, py, grade_z, profile.facade, category="facade_detail",
                ))
                index += 1
    return parts


def augment_brick_model_with_scene_architecture(
    model: BrickModel,
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> BrickModel:
    """Return a BrickModel enriched with Scene terrain, platforms and stairs."""
    has_grade = bool(scene.terrain and scene.terrain.profiles)
    if not scene.platforms and not scene.stairs and not has_grade:
        return model
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")

    _validate_exterior_primitives(scene)

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
    extra.extend(_terrain_parts(
        scene,
        origin_x=origin_x, origin_y=origin_y, origin_z=origin_z,
        studs_per_meter=studs_per_meter, plates_per_meter=plates_per_meter,
    ))
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
    width_out = max(model.width_studs + shift_x, max(part.x_studs + 1 for part in all_parts))
    depth_out = max(model.depth_studs + shift_y, max(part.y_studs + 1 for part in all_parts))
    height_out = max(model.height_plates + shift_z, max(part.z_plates + 3 for part in all_parts))
    return model.model_copy(update={"width_studs": width_out, "depth_studs": depth_out, "height_plates": height_out, "parts": all_parts})