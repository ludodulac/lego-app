"""Choose explicit LEGO footprints for ArchitecturalScene platforms.

ArchitecturalScene remains immutable and authoritative. This module makes a
representation-only decision: nearby integer footprints may improve proportional
fidelity, but only after support and stair topology pass hard gates. Platform-to-
platform contacts deliberately retain the legacy outward-ceil footprint until those
relations are solved jointly.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor

from brickhouse.scene.models import ArchitecturalScene, CONNECTIVITY_TOLERANCE_M, Platform

EPSILON = 1e-6


@dataclass(frozen=True)
class PlatformFootprintSolution:
    platform_id: str
    width_studs: int
    depth_studs: int
    target_width_studs: float
    target_depth_studs: float
    used_legacy_fallback: bool


def _round_half_up(value: float) -> int:
    return int(value + 0.5)


def _legacy_footprint(platform: Platform, studs_per_meter: float) -> tuple[int, int]:
    return (
        max(1, ceil(platform.width * studs_per_meter - EPSILON)),
        max(1, ceil(platform.depth * studs_per_meter - EPSILON)),
    )


def _scene_platforms_touch(first: Platform, second: Platform) -> bool:
    if abs(first.position.z - second.position.z) > CONNECTIVITY_TOLERANCE_M:
        return False
    ax0, ax1 = first.position.x, first.position.x + first.width
    ay0, ay1 = first.position.y, first.position.y + first.depth
    bx0, bx1 = second.position.x, second.position.x + second.width
    by0, by1 = second.position.y, second.position.y + second.depth
    x_gap = max(0.0, max(ax0, bx0) - min(ax1, bx1))
    y_gap = max(0.0, max(ay0, by0) - min(ay1, by1))
    return x_gap <= CONNECTIVITY_TOLERANCE_M and y_gap <= CONNECTIVITY_TOLERANCE_M


def _point_on_platform(point, platform: Platform) -> bool:
    return (
        platform.position.x - CONNECTIVITY_TOLERANCE_M
        <= point.x
        <= platform.position.x + platform.width + CONNECTIVITY_TOLERANCE_M
        and platform.position.y - CONNECTIVITY_TOLERANCE_M
        <= point.y
        <= platform.position.y + platform.depth + CONNECTIVITY_TOLERANCE_M
        and abs(point.z - platform.position.z) <= CONNECTIVITY_TOLERANCE_M
    )


def _candidate_values(target: float) -> tuple[int, ...]:
    low = max(1, floor(target + EPSILON))
    nearest = max(1, _round_half_up(target))
    high = max(1, ceil(target - EPSILON))
    return tuple(sorted({low, nearest, high}))


def _candidate_contains_declared_supports(
    platform: Platform,
    *,
    width: int,
    depth: int,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> bool:
    platform_x = _round_half_up((platform.position.x - origin_x) * studs_per_meter)
    platform_y = _round_half_up((platform.position.y - origin_y) * studs_per_meter)
    for support in platform.supports:
        support_x = _round_half_up((support.position.x - origin_x) * studs_per_meter)
        support_y = _round_half_up((support.position.y - origin_y) * studs_per_meter)
        support_width = max(1, ceil(support.width * studs_per_meter))
        support_depth = max(1, ceil(support.depth * studs_per_meter))
        if support_x < platform_x or support_y < platform_y:
            return False
        if support_x + support_width > platform_x + width:
            return False
        if support_y + support_depth > platform_y + depth:
            return False
    return True


def _stair_endpoint_cells(stair, point, *, origin_x, origin_y, studs_per_meter):
    endpoint_x = _round_half_up((point.x - origin_x) * studs_per_meter)
    endpoint_y = _round_half_up((point.y - origin_y) * studs_per_meter)
    stair_width = max(1, _round_half_up(stair.width * studs_per_meter))
    start_offset = -(stair_width // 2)
    dx = abs(stair.end.x - stair.start.x)
    dy = abs(stair.end.y - stair.start.y)
    if dx >= dy:
        return [
            (endpoint_x, endpoint_y + start_offset + offset)
            for offset in range(stair_width)
        ]
    return [
        (endpoint_x + start_offset + offset, endpoint_y)
        for offset in range(stair_width)
    ]


def _candidate_contains_connected_stair_endpoints(
    platform: Platform,
    scene: ArchitecturalScene,
    *,
    width: int,
    depth: int,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> bool:
    platform_x = _round_half_up((platform.position.x - origin_x) * studs_per_meter)
    platform_y = _round_half_up((platform.position.y - origin_y) * studs_per_meter)
    for stair in scene.stairs:
        for point in (stair.start, stair.end):
            if not _point_on_platform(point, platform):
                continue
            for endpoint_x, endpoint_y in _stair_endpoint_cells(
                stair,
                point,
                origin_x=origin_x,
                origin_y=origin_y,
                studs_per_meter=studs_per_meter,
            ):
                if not (
                    platform_x <= endpoint_x < platform_x + width
                    and platform_y <= endpoint_y < platform_y + depth
                ):
                    return False
    return True


def _relative_error(target: float, represented: float) -> float:
    if target <= EPSILON:
        return 0.0 if abs(represented) <= EPSILON else 1.0
    return abs(represented - target) / target


def _fidelity_key(
    width: int,
    depth: int,
    *,
    target_width: float,
    target_depth: float,
) -> tuple[float, float, float, float, int, int]:
    width_error = _relative_error(target_width, width)
    depth_error = _relative_error(target_depth, depth)
    target_aspect = target_width / target_depth
    represented_aspect = width / depth
    aspect_error = _relative_error(target_aspect, represented_aspect)
    target_area = target_width * target_depth
    area_error = _relative_error(target_area, width * depth)
    return (
        max(width_error, depth_error),
        aspect_error,
        area_error,
        width_error + depth_error,
        width,
        depth,
    )


def select_platform_footprint(
    platform: Platform,
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> PlatformFootprintSolution:
    """Return the nearest relation-safe integer footprint for one platform."""
    target_width = platform.width * studs_per_meter
    target_depth = platform.depth * studs_per_meter
    legacy_width, legacy_depth = _legacy_footprint(platform, studs_per_meter)

    if any(
        other.id != platform.id and _scene_platforms_touch(platform, other)
        for other in scene.platforms
    ):
        return PlatformFootprintSolution(
            platform.id,
            legacy_width,
            legacy_depth,
            target_width,
            target_depth,
            True,
        )

    candidates: list[tuple[int, int]] = []
    for width in _candidate_values(target_width):
        for depth in _candidate_values(target_depth):
            if not _candidate_contains_declared_supports(
                platform,
                width=width,
                depth=depth,
                origin_x=origin_x,
                origin_y=origin_y,
                studs_per_meter=studs_per_meter,
            ):
                continue
            if not _candidate_contains_connected_stair_endpoints(
                platform,
                scene,
                width=width,
                depth=depth,
                origin_x=origin_x,
                origin_y=origin_y,
                studs_per_meter=studs_per_meter,
            ):
                continue
            candidates.append((width, depth))

    if not candidates:
        width, depth = legacy_width, legacy_depth
        fallback = True
    else:
        width, depth = min(
            candidates,
            key=lambda item: _fidelity_key(
                item[0],
                item[1],
                target_width=target_width,
                target_depth=target_depth,
            ),
        )
        fallback = (width, depth) == (legacy_width, legacy_depth)

    return PlatformFootprintSolution(
        platform.id,
        width,
        depth,
        target_width,
        target_depth,
        fallback,
    )


def select_platform_footprints(
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> dict[str, PlatformFootprintSolution]:
    return {
        platform.id: select_platform_footprint(
            platform,
            scene,
            origin_x=origin_x,
            origin_y=origin_y,
            studs_per_meter=studs_per_meter,
        )
        for platform in scene.platforms
    }
