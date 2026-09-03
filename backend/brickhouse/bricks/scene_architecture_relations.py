"""Preserve validated ArchitecturalScene relations across horizontal LEGO quantization.

The base scene renderer remains responsible for geometry generation. This layer
coordinates representation-only platform host snaps with stair endpoints so one
validated relation is never repaired by breaking another. ArchitecturalScene
metric coordinates are never mutated.
"""
from __future__ import annotations

from math import ceil

from brickhouse.scene.models import ArchitecturalScene, Platform, StairRun

from .brick_model import BrickModel
from .scaling import COURSES_PER_STUD_RATIO
from . import scene_architecture as base


def _connected_platform(point, scene: ArchitecturalScene) -> Platform | None:
    """Return the same deterministic platform chosen by shared landing-level logic."""
    matches = [platform for platform in scene.platforms if base._point_on_platform(point, platform)]
    if not matches:
        return None
    return min(matches, key=lambda item: (abs(point.z - item.position.z), item.id))


def _platform_candidate_shift(
    platform: Platform,
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> tuple[int, int]:
    """Reuse BH-110's host-contact decision without its stair safety veto."""
    width = max(1, ceil(platform.width * studs_per_meter - base.EPSILON))
    depth = max(1, ceil(platform.depth * studs_per_meter - base.EPSILON))
    stairless_scene = scene.model_copy(update={"stairs": []})
    return base._platform_host_contact_shift(
        platform,
        stairless_scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
        width=width,
        depth=depth,
    )


def _endpoint_shift(
    point,
    scene: ArchitecturalScene,
    shifts: dict[str, tuple[int, int]],
) -> tuple[int, int]:
    platform = _connected_platform(point, scene)
    return shifts.get(platform.id, (0, 0)) if platform is not None else (0, 0)


def _stair_axis_preserved(
    stair: StairRun,
    scene: ArchitecturalScene,
    shifts: dict[str, tuple[int, int]],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> bool:
    """Check proposed endpoint anchors keep the Scene run axis and ordering."""
    start_shift = _endpoint_shift(stair.start, scene, shifts)
    end_shift = _endpoint_shift(stair.end, scene, shifts)
    sx = base._round_half_up((stair.start.x - origin_x) * studs_per_meter) + start_shift[0]
    sy = base._round_half_up((stair.start.y - origin_y) * studs_per_meter) + start_shift[1]
    ex = base._round_half_up((stair.end.x - origin_x) * studs_per_meter) + end_shift[0]
    ey = base._round_half_up((stair.end.y - origin_y) * studs_per_meter) + end_shift[1]

    metric_dx = stair.end.x - stair.start.x
    metric_dy = stair.end.y - stair.start.y
    if abs(metric_dx) > base.EPSILON:
        if sy != ey:
            return False
        return ex > sx if metric_dx > 0 else ex < sx
    if abs(metric_dy) > base.EPSILON:
        if sx != ex:
            return False
        return ey > sy if metric_dy > 0 else ey < sy
    return sx == ex and sy == ey


def _platform_representation_shifts(
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> dict[str, tuple[int, int]]:
    """Return globally compatible platform host snaps for this LEGO representation.

    Candidate snaps come from the exact BH-110 host-contact rule. Stair constraints
    are then solved monotonically: if current candidate endpoint shifts would change
    a run's architectural axis or ordering, every non-zero platform snap affecting
    that stair is disabled. Repeating to a fixed point handles shared platforms and
    chains of stairs deterministically without inventing a compromise geometry.
    """
    shifts = {
        platform.id: _platform_candidate_shift(
            platform,
            scene,
            origin_x=origin_x,
            origin_y=origin_y,
            studs_per_meter=studs_per_meter,
        )
        for platform in scene.platforms
    }

    while True:
        changed = False
        for stair in sorted(scene.stairs, key=lambda item: item.id):
            if _stair_axis_preserved(
                stair,
                scene,
                shifts,
                origin_x=origin_x,
                origin_y=origin_y,
                studs_per_meter=studs_per_meter,
            ):
                continue
            connected = {
                platform.id
                for point in (stair.start, stair.end)
                if (platform := _connected_platform(point, scene)) is not None
            }
            for platform_id in sorted(connected):
                if shifts.get(platform_id, (0, 0)) != (0, 0):
                    shifts[platform_id] = (0, 0)
                    changed = True
        if not changed:
            return shifts


def _shifted_point(point, shift: tuple[int, int], studs_per_meter: float):
    if shift == (0, 0):
        return point
    return point.model_copy(
        update={
            "x": point.x + shift[0] / studs_per_meter,
            "y": point.y + shift[1] / studs_per_meter,
        }
    )


def _scene_with_representation_platform_positions(
    scene: ArchitecturalScene,
    shifts: dict[str, tuple[int, int]],
    studs_per_meter: float,
) -> ArchitecturalScene:
    platforms = []
    for platform in scene.platforms:
        shift = shifts.get(platform.id, (0, 0))
        if shift == (0, 0):
            platforms.append(platform)
            continue
        position = platform.position.model_copy(
            update={
                "x": platform.position.x + shift[0] / studs_per_meter,
                "y": platform.position.y + shift[1] / studs_per_meter,
            }
        )
        platforms.append(platform.model_copy(update={"position": position}))
    return scene.model_copy(update={"platforms": platforms})


def _shifted_stair(
    stair: StairRun,
    scene: ArchitecturalScene,
    shifts: dict[str, tuple[int, int]],
    studs_per_meter: float,
) -> StairRun:
    return stair.model_copy(
        update={
            "start": _shifted_point(
                stair.start,
                _endpoint_shift(stair.start, scene, shifts),
                studs_per_meter,
            ),
            "end": _shifted_point(
                stair.end,
                _endpoint_shift(stair.end, scene, shifts),
                studs_per_meter,
            ),
        }
    )


def augment_brick_model_with_scene_architecture_relations(
    model: BrickModel,
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> BrickModel:
    """Render scene architecture while preserving compatible host/stair relations."""
    rendered = base.augment_brick_model_with_scene_architecture(
        model,
        scene,
        front_width_studs=front_width_studs,
    )
    if not scene.platforms or front_width_studs <= 0:
        return rendered

    main = scene.volumes[0]
    studs_per_meter = front_width_studs / main.width.value
    plates_per_meter = studs_per_meter * COURSES_PER_STUD_RATIO * 3
    origin_x, origin_y, origin_z = base._scene_bounds(scene)
    shifts = _platform_representation_shifts(
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    connected_platform_shifts = {
        platform.id: shifts[platform.id]
        for platform in scene.platforms
        if shifts.get(platform.id, (0, 0)) != (0, 0)
        and base._platform_has_connected_stair(platform, scene)
    }
    if not connected_platform_shifts:
        return rendered

    updated_parts = []
    for part in rendered.parts:
        moved = part
        for platform_id, (shift_x, shift_y) in connected_platform_shifts.items():
            if part.placement_id.startswith(f"scene-platform:{platform_id}:"):
                x = part.x_studs + shift_x
                y = part.y_studs + shift_y
                if x < 0 or y < 0:
                    raise ValueError("platform representation shift would leave the LEGO grid")
                moved = part.model_copy(update={"x_studs": x, "y_studs": y})
                break
        updated_parts.append(moved)

    affected_stairs = {
        stair.id
        for stair in scene.stairs
        if _endpoint_shift(stair.start, scene, shifts) != (0, 0)
        or _endpoint_shift(stair.end, scene, shifts) != (0, 0)
    }
    if affected_stairs:
        updated_parts = [
            part
            for part in updated_parts
            if not any(
                part.placement_id.startswith(f"scene-stair:{stair_id}:")
                for stair_id in affected_stairs
            )
        ]
        representation_scene = _scene_with_representation_platform_positions(
            scene,
            shifts,
            studs_per_meter,
        )
        for stair in scene.stairs:
            if stair.id not in affected_stairs:
                continue
            adjusted = _shifted_stair(stair, scene, shifts, studs_per_meter)
            updated_parts.extend(
                base._stair_parts(
                    adjusted,
                    representation_scene,
                    origin_x=origin_x,
                    origin_y=origin_y,
                    origin_z=origin_z,
                    studs_per_meter=studs_per_meter,
                    plates_per_meter=plates_per_meter,
                )
            )

    return rendered.model_copy(
        update={
            "width_studs": max(rendered.width_studs, max(part.x_studs + 1 for part in updated_parts)),
            "depth_studs": max(rendered.depth_studs, max(part.y_studs + 1 for part in updated_parts)),
            "height_plates": max(rendered.height_plates, max(part.z_plates + 3 for part in updated_parts)),
            "parts": updated_parts,
        }
    )
