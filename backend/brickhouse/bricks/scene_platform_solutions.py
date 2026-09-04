"""Select proportion-faithful LEGO footprints for ArchitecturalScene platforms.

ArchitecturalScene metric geometry is immutable.  The selected integer footprint is
representation-only and may be smaller than the old independent-ceil raster only
when doing so keeps stronger stair/support relations intact.  Platform-to-platform
contacts deliberately retain the legacy footprint until they can be optimized
jointly.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor, log

from brickhouse.scene.models import (
    ArchitecturalScene,
    CONNECTIVITY_TOLERANCE_M,
    Platform,
)


EPSILON = 1e-6


@dataclass(frozen=True)
class PlatformFootprintSolution:
    platform_id: str
    target_width_studs: float
    target_depth_studs: float
    width_studs: int
    depth_studs: int
    legacy_width_studs: int
    legacy_depth_studs: int
    dimensional_error: float
    aspect_ratio_error: float
    area_error: float
    score: float
    constraint_reason: str | None = None

    @property
    def legacy_changed(self) -> bool:
        return (
            self.width_studs != self.legacy_width_studs
            or self.depth_studs != self.legacy_depth_studs
        )


def _round_half_up(value: float) -> int:
    return int(value + 0.5)


def _candidate_axis(target: float) -> tuple[int, ...]:
    lower = max(1, floor(target) - 1)
    upper = max(1, ceil(target) + 1)
    return tuple(range(lower, upper + 1))


def _score(
    target_width: float,
    target_depth: float,
    width: int,
    depth: int,
) -> tuple[float, float, float, float]:
    dimensional_error = 0.5 * (
        abs(width - target_width) / target_width
        + abs(depth - target_depth) / target_depth
    )
    target_ratio = target_width / target_depth
    candidate_ratio = width / depth
    aspect_ratio_error = abs(log(candidate_ratio / target_ratio))
    target_area = target_width * target_depth
    area_error = abs(width * depth - target_area) / target_area
    score = 0.50 * dimensional_error + 0.35 * aspect_ratio_error + 0.15 * area_error
    return score, dimensional_error, aspect_ratio_error, area_error


def _platforms_touch(first: Platform, second: Platform) -> bool:
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


def _required_raster_bounds(
    platform: Platform,
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> tuple[int, int, int, int] | None:
    """Return cells that a candidate must cover to preserve declared local relations."""
    required: list[tuple[int, int, int, int]] = []

    for support in platform.supports:
        x0 = _round_half_up((support.position.x - origin_x) * studs_per_meter)
        y0 = _round_half_up((support.position.y - origin_y) * studs_per_meter)
        width = max(1, ceil(support.width * studs_per_meter))
        depth = max(1, ceil(support.depth * studs_per_meter))
        required.append((x0, y0, x0 + width - 1, y0 + depth - 1))

    for stair in scene.stairs:
        for point in (stair.start, stair.end):
            if not _point_on_platform(point, platform):
                continue
            x = _round_half_up((point.x - origin_x) * studs_per_meter)
            y = _round_half_up((point.y - origin_y) * studs_per_meter)
            required.append((x, y, x, y))

    if not required:
        return None
    return (
        min(item[0] for item in required),
        min(item[1] for item in required),
        max(item[2] for item in required),
        max(item[3] for item in required),
    )


def _solution(
    platform: Platform,
    *,
    target_width: float,
    target_depth: float,
    width: int,
    depth: int,
    legacy_width: int,
    legacy_depth: int,
    constraint_reason: str | None = None,
) -> PlatformFootprintSolution:
    score, dimensional_error, aspect_ratio_error, area_error = _score(
        target_width,
        target_depth,
        width,
        depth,
    )
    return PlatformFootprintSolution(
        platform_id=platform.id,
        target_width_studs=target_width,
        target_depth_studs=target_depth,
        width_studs=width,
        depth_studs=depth,
        legacy_width_studs=legacy_width,
        legacy_depth_studs=legacy_depth,
        dimensional_error=dimensional_error,
        aspect_ratio_error=aspect_ratio_error,
        area_error=area_error,
        score=score,
        constraint_reason=constraint_reason,
    )


def select_platform_footprint(
    platform: Platform,
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> PlatformFootprintSolution:
    """Choose the best safe integer footprint for one declared Scene platform."""
    if studs_per_meter <= 0:
        raise ValueError("studs_per_meter must be positive")

    target_width = platform.width * studs_per_meter
    target_depth = platform.depth * studs_per_meter
    legacy_width = max(1, ceil(target_width - EPSILON))
    legacy_depth = max(1, ceil(target_depth - EPSILON))

    if any(
        other.id != platform.id and _platforms_touch(platform, other)
        for other in scene.platforms
    ):
        return _solution(
            platform,
            target_width=target_width,
            target_depth=target_depth,
            width=legacy_width,
            depth=legacy_depth,
            legacy_width=legacy_width,
            legacy_depth=legacy_depth,
            constraint_reason="platform_contact_legacy_fallback",
        )

    x0 = _round_half_up((platform.position.x - origin_x) * studs_per_meter)
    y0 = _round_half_up((platform.position.y - origin_y) * studs_per_meter)
    required = _required_raster_bounds(
        platform,
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )

    ranked: list[
        tuple[
            tuple[float, float, float, float, int, int, int],
            PlatformFootprintSolution,
        ]
    ] = []
    for width in _candidate_axis(target_width):
        for depth in _candidate_axis(target_depth):
            if required is not None:
                req_x0, req_y0, req_x1, req_y1 = required
                if (
                    req_x0 < x0
                    or req_y0 < y0
                    or req_x1 >= x0 + width
                    or req_y1 >= y0 + depth
                ):
                    continue
            solution = _solution(
                platform,
                target_width=target_width,
                target_depth=target_depth,
                width=width,
                depth=depth,
                legacy_width=legacy_width,
                legacy_depth=legacy_depth,
            )
            key = (
                round(solution.score, 12),
                round(solution.aspect_ratio_error, 12),
                round(solution.dimensional_error, 12),
                round(solution.area_error, 12),
                width * depth,
                width,
                depth,
            )
            ranked.append((key, solution))

    if ranked:
        return min(ranked, key=lambda item: item[0])[1]

    return _solution(
        platform,
        target_width=target_width,
        target_depth=target_depth,
        width=legacy_width,
        depth=legacy_depth,
        legacy_width=legacy_width,
        legacy_depth=legacy_depth,
        constraint_reason="local_constraints_need_position_solver",
    )
