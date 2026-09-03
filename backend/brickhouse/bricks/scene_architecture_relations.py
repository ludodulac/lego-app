"""Preserve validated ArchitecturalScene relations across horizontal LEGO quantization.

The base scene renderer remains responsible for geometry generation. This layer
coordinates representation-only platform host snaps and direct volume-boundary
contacts with stair endpoints so one validated relation is never repaired by
breaking another. ArchitecturalScene metric coordinates are never mutated.
"""
from __future__ import annotations

from math import ceil

from brickhouse.building.models import Facade
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


def _connected_volume_boundary(point, scene: ArchitecturalScene):
    """Return the deterministic Scene volume/facade already touched by ``point``."""
    matches = []
    for volume in scene.volumes:
        if not scene._point_on_volume_boundary(point, volume):
            continue
        x0 = volume.position.x
        x1 = x0 + volume.width.value
        y0 = volume.position.y
        y1 = y0 + volume.depth.value
        boundaries = (
            (abs(point.x - x0), Facade.LEFT),
            (abs(point.x - x1), Facade.RIGHT),
            (abs(point.y - y0), Facade.FRONT),
            (abs(point.y - y1), Facade.REAR),
        )
        distance, facade = min(boundaries, key=lambda item: (item[0], item[1].value))
        matches.append((distance, volume.id, facade.value, volume, facade))
    if not matches:
        return None
    _, _, _, volume, facade = min(matches, key=lambda item: item[:3])
    return volume, facade


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


def _platform_endpoint_shift(
    point,
    scene: ArchitecturalScene,
    shifts: dict[str, tuple[int, int]],
) -> tuple[int, int]:
    platform = _connected_platform(point, scene)
    return shifts.get(platform.id, (0, 0)) if platform is not None else (0, 0)


def _volume_endpoint_shift(
    point,
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> tuple[int, int]:
    """Snap an unambiguous Scene-valid stair endpoint to a quantized volume boundary.

    Platform and ground contacts are stronger endpoint interpretations in the Scene
    contract. A point already connected by either must not be reinterpreted as a
    building-boundary connection merely because it also lies inside the tolerance.
    """
    if _connected_platform(point, scene) is not None or point.z <= base.CONNECTIVITY_TOLERANCE_M:
        return 0, 0
    connection = _connected_volume_boundary(point, scene)
    if connection is None:
        return 0, 0
    volume, facade = connection
    current_x = base._round_half_up((point.x - origin_x) * studs_per_meter)
    current_y = base._round_half_up((point.y - origin_y) * studs_per_meter)
    if facade is Facade.LEFT:
        target = base._round_half_up((volume.position.x - origin_x) * studs_per_meter)
        return target - current_x, 0
    if facade is Facade.RIGHT:
        target = base._round_half_up(
            (volume.position.x + volume.width.value - origin_x) * studs_per_meter
        )
        return target - current_x, 0
    if facade is Facade.FRONT:
        target = base._round_half_up((volume.position.y - origin_y) * studs_per_meter)
        return 0, target - current_y
    target = base._round_half_up(
        (volume.position.y + volume.depth.value - origin_y) * studs_per_meter
    )
    return 0, target - current_y


def _proposed_endpoint_shift(
    point,
    scene: ArchitecturalScene,
    shifts: dict[str, tuple[int, int]],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> tuple[int, int]:
    platform = _connected_platform(point, scene)
    if platform is not None:
        return shifts.get(platform.id, (0, 0))
    return _volume_endpoint_shift(
        point,
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )


def _axis_preserved_for_endpoint_shifts(
    stair: StairRun,
    *,
    start_shift: tuple[int, int],
    end_shift: tuple[int, int],
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> bool:
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


def _stair_proposed_endpoint_shifts(
    stair: StairRun,
    scene: ArchitecturalScene,
    shifts: dict[str, tuple[int, int]],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> tuple[tuple[int, int], tuple[int, int]]:
    return (
        _proposed_endpoint_shift(
            stair.start,
            scene,
            shifts,
            origin_x=origin_x,
            origin_y=origin_y,
            studs_per_meter=studs_per_meter,
        ),
        _proposed_endpoint_shift(
            stair.end,
            scene,
            shifts,
            origin_x=origin_x,
            origin_y=origin_y,
            studs_per_meter=studs_per_meter,
        ),
    )


def _stair_axis_preserved(
    stair: StairRun,
    scene: ArchitecturalScene,
    shifts: dict[str, tuple[int, int]],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> bool:
    """Check all proposed relation anchors keep the Scene run axis and ordering."""
    start_shift, end_shift = _stair_proposed_endpoint_shifts(
        stair,
        scene,
        shifts,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    return _axis_preserved_for_endpoint_shifts(
        stair,
        start_shift=start_shift,
        end_shift=end_shift,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )


def _platform_representation_shifts(
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> dict[str, tuple[int, int]]:
    """Return globally compatible platform host snaps for this LEGO representation.

    Candidate snaps come from the exact BH-110 host-contact rule. Stair constraints,
    including direct Scene-valid volume-boundary anchors, are then solved monotonically:
    if the current candidates would change a run's architectural axis or ordering,
    every non-zero platform snap affecting that stair is disabled. Direct volume
    anchors are never forced; a still-incompatible volume anchor is dropped later.
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


def _safe_stair_endpoint_shifts(
    stair: StairRun,
    scene: ArchitecturalScene,
    shifts: dict[str, tuple[int, int]],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """Use direct volume anchors only when they preserve the run's identity."""
    proposed = _stair_proposed_endpoint_shifts(
        stair,
        scene,
        shifts,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    if _axis_preserved_for_endpoint_shifts(
        stair,
        start_shift=proposed[0],
        end_shift=proposed[1],
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    ):
        return proposed

    platform_only = (
        _platform_endpoint_shift(stair.start, scene, shifts),
        _platform_endpoint_shift(stair.end, scene, shifts),
    )
    if _axis_preserved_for_endpoint_shifts(
        stair,
        start_shift=platform_only[0],
        end_shift=platform_only[1],
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    ):
        return platform_only
    return (0, 0), (0, 0)


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
    *,
    start_shift: tuple[int, int],
    end_shift: tuple[int, int],
    studs_per_meter: float,
) -> StairRun:
    return stair.model_copy(
        update={
            "start": _shifted_point(stair.start, start_shift, studs_per_meter),
            "end": _shifted_point(stair.end, end_shift, studs_per_meter),
        }
    )


def augment_brick_model_with_scene_architecture_relations(
    model: BrickModel,
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> BrickModel:
    """Render scene architecture while preserving compatible horizontal relations."""
    rendered = base.augment_brick_model_with_scene_architecture(
        model,
        scene,
        front_width_studs=front_width_studs,
    )
    if front_width_studs <= 0:
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
    stair_endpoint_shifts = {
        stair.id: _safe_stair_endpoint_shifts(
            stair,
            scene,
            shifts,
            origin_x=origin_x,
            origin_y=origin_y,
            studs_per_meter=studs_per_meter,
        )
        for stair in scene.stairs
    }
    affected_stairs = {
        stair_id
        for stair_id, (start_shift, end_shift) in stair_endpoint_shifts.items()
        if start_shift != (0, 0) or end_shift != (0, 0)
    }
    if not connected_platform_shifts and not affected_stairs:
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
            start_shift, end_shift = stair_endpoint_shifts[stair.id]
            adjusted = _shifted_stair(
                stair,
                start_shift=start_shift,
                end_shift=end_shift,
                studs_per_meter=studs_per_meter,
            )
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
