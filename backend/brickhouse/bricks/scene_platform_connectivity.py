"""Preserve and audit platform connectivity across LEGO quantization.

The general ArchitecturalScene relation stage remains authoritative for platform↔host
and stair endpoint anchors. This layer propagates an already-rooted horizontal
representation through unambiguous coplanar platform contacts, then reports any
Scene-valid platform contact that still cannot be represented faithfully. Metric Scene
geometry is never mutated and floating platform-only components are deliberately left
alone.
"""
from __future__ import annotations

from math import ceil

from brickhouse.scene.models import ArchitecturalScene, Platform

from . import scene_architecture as base
from .brick_model import BrickModel
from .export import BrickExportFidelityIssue
from .scaling import COURSES_PER_STUD_RATIO
from .scene_architecture_relations import (
    _platform_candidate_shift,
    _platform_representation_shifts,
    augment_brick_model_with_scene_architecture_relations,
)


def _platform_touches_volume(platform: Platform, scene: ArchitecturalScene) -> bool:
    px0 = platform.position.x
    px1 = px0 + platform.width
    py0 = platform.position.y
    py1 = py0 + platform.depth
    for volume in scene.volumes:
        if volume.width.value is None or volume.depth.value is None:
            continue
        vx0 = volume.position.x
        vx1 = vx0 + volume.width.value
        vy0 = volume.position.y
        vy1 = vy0 + volume.depth.value
        x_overlap = min(px1, vx1) >= max(px0, vx0) - base.CONNECTIVITY_TOLERANCE_M
        y_overlap = min(py1, vy1) >= max(py0, vy0) - base.CONNECTIVITY_TOLERANCE_M
        if (
            min(abs(px0 - vx1), abs(px1 - vx0)) <= base.CONNECTIVITY_TOLERANCE_M
            and y_overlap
        ) or (
            min(abs(py0 - vy1), abs(py1 - vy0)) <= base.CONNECTIVITY_TOLERANCE_M
            and x_overlap
        ):
            return True
    return False


def _strong_platform_roots(scene: ArchitecturalScene) -> set[str]:
    """Return platforms whose position is constrained by building or stair geometry."""
    return {
        platform.id
        for platform in scene.platforms
        if _platform_touches_volume(platform, scene)
        or base._platform_has_connected_stair(platform, scene)
    }


def _scene_platforms_touch(first: Platform, second: Platform) -> bool:
    """Mirror the Scene platform-connectivity tolerance without changing its truth."""
    if abs(first.position.z - second.position.z) > base.CONNECTIVITY_TOLERANCE_M:
        return False
    ax0, ax1 = first.position.x, first.position.x + first.width
    ay0, ay1 = first.position.y, first.position.y + first.depth
    bx0, bx1 = second.position.x, second.position.x + second.width
    by0, by1 = second.position.y, second.position.y + second.depth
    x_gap = max(0.0, max(ax0, bx0) - min(ax1, bx1))
    y_gap = max(0.0, max(ay0, by0) - min(ay1, by1))
    return x_gap <= base.CONNECTIVITY_TOLERANCE_M and y_gap <= base.CONNECTIVITY_TOLERANCE_M


def _metric_contact_axis(first: Platform, second: Platform) -> str | None:
    """Return the normal direction from first toward second for an edge-like contact.

    The Scene tolerance also admits near-corner contacts. They are intentionally not
    converted into an edge relation here because choosing an X or Y snap would invent
    architectural intent. Real overlap on the orthogonal metric axis is required.
    """
    if abs(first.position.z - second.position.z) > base.CONNECTIVITY_TOLERANCE_M:
        return None
    ax0 = first.position.x
    ax1 = ax0 + first.width
    ay0 = first.position.y
    ay1 = ay0 + first.depth
    bx0 = second.position.x
    bx1 = bx0 + second.width
    by0 = second.position.y
    by1 = by0 + second.depth
    x_overlap = min(ax1, bx1) - max(ax0, bx0)
    y_overlap = min(ay1, by1) - max(ay0, by0)

    if y_overlap > base.EPSILON:
        if ax1 <= bx0 + base.EPSILON and 0 <= bx0 - ax1 <= base.CONNECTIVITY_TOLERANCE_M:
            return "x_positive"
        if ax0 >= bx1 - base.EPSILON and 0 <= ax0 - bx1 <= base.CONNECTIVITY_TOLERANCE_M:
            return "x_negative"
    if x_overlap > base.EPSILON:
        if ay1 <= by0 + base.EPSILON and 0 <= by0 - ay1 <= base.CONNECTIVITY_TOLERANCE_M:
            return "y_positive"
        if ay0 >= by1 - base.EPSILON and 0 <= ay0 - by1 <= base.CONNECTIVITY_TOLERANCE_M:
            return "y_negative"
    return None


def _platform_raster_rect(
    platform: Platform,
    shift: tuple[int, int],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> tuple[int, int, int, int]:
    x0 = base._round_half_up((platform.position.x - origin_x) * studs_per_meter) + shift[0]
    y0 = base._round_half_up((platform.position.y - origin_y) * studs_per_meter) + shift[1]
    width = max(1, ceil(platform.width * studs_per_meter - base.EPSILON))
    depth = max(1, ceil(platform.depth * studs_per_meter - base.EPSILON))
    return x0, y0, width, depth


def _intervals_overlap(first0: int, first1: int, second0: int, second1: int) -> bool:
    return max(first0, second0) <= min(first1, second1)


def _contact_shift(
    moving: Platform,
    fixed: Platform,
    shifts: dict[str, tuple[int, int]],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> tuple[int, int] | None:
    """Return the minimum gap-closing shift, zero if contact already survives, or None.

    ``None`` means the metric relation cannot be repaired by a single facade-normal
    translation without also inventing orthogonal overlap.
    """
    axis = _metric_contact_axis(moving, fixed)
    if axis is None:
        return None
    mx, my, mw, md = _platform_raster_rect(
        moving,
        shifts.get(moving.id, (0, 0)),
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    fx, fy, fw, fd = _platform_raster_rect(
        fixed,
        shifts.get(fixed.id, (0, 0)),
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    if axis.startswith("x_"):
        if not _intervals_overlap(my, my + md - 1, fy, fy + fd - 1):
            return None
        if axis == "x_positive":
            if mx + mw >= fx:
                return 0, 0
            return fx - (mx + mw), 0
        if fx + fw >= mx:
            return 0, 0
        return fx + fw - mx, 0

    if not _intervals_overlap(mx, mx + mw - 1, fx, fx + fw - 1):
        return None
    if axis == "y_positive":
        if my + md >= fy:
            return 0, 0
        return 0, fy - (my + md)
    if fy + fd >= my:
        return 0, 0
    return 0, fy + fd - my


def _rooted_platform_pair_shifts(
    scene: ArchitecturalScene,
    existing_shifts: dict[str, tuple[int, int]],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> dict[str, tuple[int, int]]:
    """Propagate compatible platform contact shifts outward from strong roots."""
    by_id = {platform.id: platform for platform in scene.platforms}
    rooted = _strong_platform_roots(scene)
    combined = {platform.id: existing_shifts.get(platform.id, (0, 0)) for platform in scene.platforms}
    extra = {platform.id: (0, 0) for platform in scene.platforms}

    contacts: dict[str, set[str]] = {platform.id: set() for platform in scene.platforms}
    for index, first in enumerate(scene.platforms):
        for second in scene.platforms[index + 1 :]:
            if _metric_contact_axis(first, second) is None and _metric_contact_axis(second, first) is None:
                continue
            contacts[first.id].add(second.id)
            contacts[second.id].add(first.id)

    while True:
        progress = False
        for platform_id in sorted(by_id):
            if platform_id in rooted:
                continue
            rooted_neighbors = sorted(neighbor for neighbor in contacts[platform_id] if neighbor in rooted)
            if not rooted_neighbors:
                continue
            candidates = []
            invalid = False
            for neighbor_id in rooted_neighbors:
                candidate = _contact_shift(
                    by_id[platform_id],
                    by_id[neighbor_id],
                    combined,
                    origin_x=origin_x,
                    origin_y=origin_y,
                    studs_per_meter=studs_per_meter,
                )
                if candidate is None:
                    invalid = True
                    break
                candidates.append(candidate)
            if invalid or not candidates or len(set(candidates)) != 1:
                continue
            delta = candidates[0]
            current = combined[platform_id]
            proposed = current[0] + delta[0], current[1] + delta[1]
            x0, y0, _, _ = _platform_raster_rect(
                by_id[platform_id],
                proposed,
                origin_x=origin_x,
                origin_y=origin_y,
                studs_per_meter=studs_per_meter,
            )
            if x0 < 0 or y0 < 0:
                continue
            combined[platform_id] = proposed
            extra[platform_id] = delta
            rooted.add(platform_id)
            progress = True
        if not progress:
            return extra


def _raster_contact_preserved(
    first: Platform,
    second: Platform,
    shifts: dict[str, tuple[int, int]],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> bool:
    ax, ay, aw, ad = _platform_raster_rect(
        first,
        shifts.get(first.id, (0, 0)),
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    bx, by, bw, bd = _platform_raster_rect(
        second,
        shifts.get(second.id, (0, 0)),
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    ax1, ay1 = ax + aw - 1, ay + ad - 1
    bx1, by1 = bx + bw - 1, by + bd - 1
    overlap_x = _intervals_overlap(ax, ax1, bx, bx1)
    overlap_y = _intervals_overlap(ay, ay1, by, by1)
    adjacent_x = ax1 + 1 == bx or bx1 + 1 == ax
    adjacent_y = ay1 + 1 == by or by1 + 1 == ay
    return (overlap_x and (overlap_y or adjacent_y)) or (overlap_y and adjacent_x)


def _candidate_host_facade(candidate: tuple[int, int]) -> str:
    shift_x, shift_y = candidate
    if shift_x > 0:
        return "left"
    if shift_x < 0:
        return "right"
    if shift_y > 0:
        return "front"
    if shift_y < 0:
        return "rear"
    raise ValueError("host contact facade requires a non-zero candidate shift")


def _platform_host_fidelity_issues(
    scene: ArchitecturalScene,
    shifts: dict[str, tuple[int, int]],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> list[BrickExportFidelityIssue]:
    """Report host contacts whose required BH-110 snap was conservatively refused."""
    issues: list[BrickExportFidelityIssue] = []
    main = scene.volumes[0]
    for platform in scene.platforms:
        candidate = _platform_candidate_shift(
            platform,
            scene,
            origin_x=origin_x,
            origin_y=origin_y,
            studs_per_meter=studs_per_meter,
        )
        if candidate == (0, 0) or shifts.get(platform.id, (0, 0)) == candidate:
            continue
        host_volume_id = getattr(platform, "host_volume_id", None) or main.id
        facade = _candidate_host_facade(candidate)
        issues.append(
            BrickExportFidelityIssue(
                code="lego_platform_host_contact_not_preserved",
                severity="warning",
                object_id=platform.id,
                message=(
                    f"ArchitecturalScene places platform {platform.id!r} against {facade} facade of "
                    f"host volume {host_volume_id!r}, but the conservative LEGO relation solver leaves "
                    "their horizontal raster disconnected because applying the required host snap would "
                    "break a stronger stair relation. Source platform geometry remains unchanged."
                ),
            )
        )
    return issues


def platform_connectivity_fidelity_issues(
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> list[BrickExportFidelityIssue]:
    """Report Scene-valid platform contacts not preserved by the final LEGO raster."""
    if front_width_studs <= 0 or not scene.platforms:
        return []
    main = scene.volumes[0]
    studs_per_meter = front_width_studs / main.width.value
    plates_per_meter = studs_per_meter * COURSES_PER_STUD_RATIO * 3
    origin_x, origin_y, origin_z = base._scene_bounds(scene)
    existing = _platform_representation_shifts(
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    issues = _platform_host_fidelity_issues(
        scene,
        existing,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    if len(scene.platforms) < 2:
        return issues

    extra = _rooted_platform_pair_shifts(
        scene,
        existing,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    combined = {
        platform.id: (
            existing.get(platform.id, (0, 0))[0] + extra.get(platform.id, (0, 0))[0],
            existing.get(platform.id, (0, 0))[1] + extra.get(platform.id, (0, 0))[1],
        )
        for platform in scene.platforms
    }

    for index, first in enumerate(scene.platforms):
        for second in scene.platforms[index + 1 :]:
            if not _scene_platforms_touch(first, second):
                continue
            first_course = base._course_z(first.position.z, origin_z, plates_per_meter)
            second_course = base._course_z(second.position.z, origin_z, plates_per_meter)
            if first_course != second_course:
                issues.append(
                    BrickExportFidelityIssue(
                        code="lego_platform_contact_level_not_preserved",
                        severity="warning",
                        object_id=first.id,
                        message=(
                            f"ArchitecturalScene treats platforms {first.id!r} and {second.id!r} as connected, "
                            f"but their LEGO walkable surfaces quantize to different courses "
                            f"({first_course} vs {second_course} plates). Source platform levels remain unchanged."
                        ),
                    )
                )
            if not _raster_contact_preserved(
                first,
                second,
                combined,
                origin_x=origin_x,
                origin_y=origin_y,
                studs_per_meter=studs_per_meter,
            ):
                issues.append(
                    BrickExportFidelityIssue(
                        code="lego_platform_contact_not_preserved",
                        severity="warning",
                        object_id=first.id,
                        message=(
                            f"ArchitecturalScene treats platforms {first.id!r} and {second.id!r} as connected, "
                            "but the conservative LEGO relation solver leaves their horizontal raster disconnected. "
                            "No bridge or arbitrary platform movement was invented."
                        ),
                    )
                )
    return issues


def augment_brick_model_with_scene_platform_connectivity(
    model: BrickModel,
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> BrickModel:
    """Render scene relations and preserve rooted platform-to-platform contact."""
    rendered = augment_brick_model_with_scene_architecture_relations(
        model,
        scene,
        front_width_studs=front_width_studs,
    )
    if front_width_studs <= 0 or len(scene.platforms) < 2:
        return rendered

    main = scene.volumes[0]
    studs_per_meter = front_width_studs / main.width.value
    origin_x, origin_y, _ = base._scene_bounds(scene)
    existing = _platform_representation_shifts(
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    extra = _rooted_platform_pair_shifts(
        scene,
        existing,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    moved = {platform_id: shift for platform_id, shift in extra.items() if shift != (0, 0)}
    if not moved:
        return rendered

    updated_parts = []
    for part in rendered.parts:
        replacement = part
        for platform_id, (shift_x, shift_y) in moved.items():
            if part.placement_id.startswith(f"scene-platform:{platform_id}:"):
                x = part.x_studs + shift_x
                y = part.y_studs + shift_y
                if x < 0 or y < 0:
                    raise ValueError("platform connectivity shift would leave the LEGO grid")
                replacement = part.model_copy(update={"x_studs": x, "y_studs": y})
                break
        updated_parts.append(replacement)

    return rendered.model_copy(
        update={
            "width_studs": max(rendered.width_studs, max(part.x_studs + 1 for part in updated_parts)),
            "depth_studs": max(rendered.depth_studs, max(part.y_studs + 1 for part in updated_parts)),
            "height_plates": max(rendered.height_plates, max(part.z_plates + 3 for part in updated_parts)),
            "parts": updated_parts,
        }
    )