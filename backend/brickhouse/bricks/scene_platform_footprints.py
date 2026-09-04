"""Choose explicit LEGO footprints for ArchitecturalScene platforms.

ArchitecturalScene remains immutable and authoritative. Nearby integer footprints may
improve proportional fidelity only after support, stair and platform-contact topology
pass hard gates. Contacting platforms are solved as a representation group so one
local improvement cannot silently break a stronger architectural relation.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
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


def _valid_candidates(
    platform: Platform,
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> tuple[tuple[int, int], ...]:
    target_width = platform.width * studs_per_meter
    target_depth = platform.depth * studs_per_meter
    candidates = []
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
    if candidates:
        return tuple(candidates)
    return (_legacy_footprint(platform, studs_per_meter),)


def _raster_rect(
    platform: Platform,
    width: int,
    depth: int,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> tuple[int, int, int, int]:
    return (
        _round_half_up((platform.position.x - origin_x) * studs_per_meter),
        _round_half_up((platform.position.y - origin_y) * studs_per_meter),
        width,
        depth,
    )


def _raster_platforms_touch(
    first: Platform,
    first_size: tuple[int, int],
    second: Platform,
    second_size: tuple[int, int],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> bool:
    if abs(first.position.z - second.position.z) > CONNECTIVITY_TOLERANCE_M:
        return False
    ax, ay, aw, ad = _raster_rect(
        first,
        first_size[0],
        first_size[1],
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    bx, by, bw, bd = _raster_rect(
        second,
        second_size[0],
        second_size[1],
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    return max(ax, bx) <= min(ax + aw, bx + bw) and max(ay, by) <= min(ay + ad, by + bd)


def _contact_components(scene: ArchitecturalScene) -> tuple[tuple[Platform, ...], ...]:
    by_id = {platform.id: platform for platform in scene.platforms}
    neighbors = {platform.id: set() for platform in scene.platforms}
    for index, first in enumerate(scene.platforms):
        for second in scene.platforms[index + 1 :]:
            if _scene_platforms_touch(first, second):
                neighbors[first.id].add(second.id)
                neighbors[second.id].add(first.id)

    components = []
    remaining = set(by_id)
    while remaining:
        root = min(remaining)
        stack = [root]
        ids = set()
        while stack:
            platform_id = stack.pop()
            if platform_id in ids:
                continue
            ids.add(platform_id)
            stack.extend(sorted(neighbors[platform_id] - ids, reverse=True))
        remaining -= ids
        components.append(tuple(by_id[platform_id] for platform_id in sorted(ids)))
    return tuple(components)


def _joint_fidelity_key(
    component: tuple[Platform, ...],
    sizes: tuple[tuple[int, int], ...],
    *,
    studs_per_meter: float,
):
    dimension_errors = []
    aspect_errors = []
    area_errors = []
    aggregate_errors = []
    for platform, (width, depth) in zip(component, sizes):
        target_width = platform.width * studs_per_meter
        target_depth = platform.depth * studs_per_meter
        width_error = _relative_error(target_width, width)
        depth_error = _relative_error(target_depth, depth)
        aspect_error = _relative_error(target_width / target_depth, width / depth)
        area_error = _relative_error(target_width * target_depth, width * depth)
        dimension_errors.append(max(width_error, depth_error))
        aspect_errors.append(aspect_error)
        area_errors.append(area_error)
        aggregate_errors.append(width_error + depth_error)
    return (
        max(dimension_errors),
        max(aspect_errors),
        max(area_errors),
        sum(aggregate_errors),
        sum(aspect_errors),
        sum(area_errors),
        tuple((platform.id, size[0], size[1]) for platform, size in zip(component, sizes)),
    )


def _component_topology_preserved(
    component: tuple[Platform, ...],
    sizes: tuple[tuple[int, int], ...],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> bool:
    for index, first in enumerate(component):
        for second_index in range(index + 1, len(component)):
            second = component[second_index]
            if _scene_platforms_touch(first, second) != _raster_platforms_touch(
                first,
                sizes[index],
                second,
                sizes[second_index],
                origin_x=origin_x,
                origin_y=origin_y,
                studs_per_meter=studs_per_meter,
            ):
                return False
    return True


def _solution(
    platform: Platform,
    size: tuple[int, int],
    *,
    studs_per_meter: float,
) -> PlatformFootprintSolution:
    legacy = _legacy_footprint(platform, studs_per_meter)
    return PlatformFootprintSolution(
        platform.id,
        size[0],
        size[1],
        platform.width * studs_per_meter,
        platform.depth * studs_per_meter,
        size == legacy,
    )


def _select_isolated_platform_footprint(
    platform: Platform,
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> PlatformFootprintSolution:
    target_width = platform.width * studs_per_meter
    target_depth = platform.depth * studs_per_meter
    candidates = _valid_candidates(
        platform,
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    size = min(
        candidates,
        key=lambda item: _fidelity_key(
            item[0],
            item[1],
            target_width=target_width,
            target_depth=target_depth,
        ),
    )
    return _solution(platform, size, studs_per_meter=studs_per_meter)


def _select_component_footprints(
    component: tuple[Platform, ...],
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> dict[str, PlatformFootprintSolution]:
    if len(component) == 1:
        platform = component[0]
        return {
            platform.id: _select_isolated_platform_footprint(
                platform,
                scene,
                origin_x=origin_x,
                origin_y=origin_y,
                studs_per_meter=studs_per_meter,
            )
        }

    candidate_sets = [
        _valid_candidates(
            platform,
            scene,
            origin_x=origin_x,
            origin_y=origin_y,
            studs_per_meter=studs_per_meter,
        )
        for platform in component
    ]
    viable = [
        sizes
        for sizes in product(*candidate_sets)
        if _component_topology_preserved(
            component,
            sizes,
            origin_x=origin_x,
            origin_y=origin_y,
            studs_per_meter=studs_per_meter,
        )
    ]
    if viable:
        selected = min(
            viable,
            key=lambda sizes: _joint_fidelity_key(
                component,
                sizes,
                studs_per_meter=studs_per_meter,
            ),
        )
    else:
        selected = tuple(_legacy_footprint(platform, studs_per_meter) for platform in component)

    return {
        platform.id: _solution(platform, size, studs_per_meter=studs_per_meter)
        for platform, size in zip(component, selected)
    }


def select_platform_footprint(
    platform: Platform,
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> PlatformFootprintSolution:
    """Return the shared relation-safe footprint chosen for one platform."""
    return select_platform_footprints(
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )[platform.id]


def select_platform_footprints(
    scene: ArchitecturalScene,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> dict[str, PlatformFootprintSolution]:
    solutions = {}
    for component in _contact_components(scene):
        solutions.update(
            _select_component_footprints(
                component,
                scene,
                origin_x=origin_x,
                origin_y=origin_y,
                studs_per_meter=studs_per_meter,
            )
        )
    return solutions
