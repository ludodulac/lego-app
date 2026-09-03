"""Audit StairRun endpoint connectivity after conservative LEGO relation anchoring.

BH-111/BH-112 own representation decisions. This module only reports when the
final derived raster no longer preserves a Scene-valid endpoint relation; it never
changes ArchitecturalScene geometry or invents a compensating connection.
"""
from __future__ import annotations

from math import ceil

from brickhouse.building.models import Facade
from brickhouse.scene.models import ArchitecturalScene, Platform

from . import scene_architecture as base
from .export import BrickExportFidelityIssue
from .scene_architecture_relations import (
    _connected_platform,
    _connected_volume_boundary,
    _platform_representation_shifts,
    _safe_stair_endpoint_shifts,
)


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


def _endpoint_raster(
    point,
    shift: tuple[int, int],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> tuple[int, int]:
    return (
        base._round_half_up((point.x - origin_x) * studs_per_meter) + shift[0],
        base._round_half_up((point.y - origin_y) * studs_per_meter) + shift[1],
    )


def _point_inside_platform_raster(
    x: int,
    y: int,
    platform: Platform,
    platform_shift: tuple[int, int],
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> bool:
    px, py, width, depth = _platform_raster_rect(
        platform,
        platform_shift,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    return px <= x < px + width and py <= y < py + depth


def _volume_boundary_target(
    volume,
    facade: Facade,
    *,
    origin_x: float,
    origin_y: float,
    studs_per_meter: float,
) -> tuple[str, int]:
    if facade is Facade.LEFT:
        return "x", base._round_half_up((volume.position.x - origin_x) * studs_per_meter)
    if facade is Facade.RIGHT:
        return "x", base._round_half_up(
            (volume.position.x + volume.width.value - origin_x) * studs_per_meter
        )
    if facade is Facade.FRONT:
        return "y", base._round_half_up((volume.position.y - origin_y) * studs_per_meter)
    return "y", base._round_half_up(
        (volume.position.y + volume.depth.value - origin_y) * studs_per_meter
    )


def stair_connectivity_fidelity_issues(
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> list[BrickExportFidelityIssue]:
    """Report Scene-valid stair endpoint relations lost in the final LEGO raster."""
    if front_width_studs <= 0 or not scene.stairs:
        return []

    main = scene.volumes[0]
    studs_per_meter = front_width_studs / main.width.value
    origin_x, origin_y, _ = base._scene_bounds(scene)
    platform_shifts = _platform_representation_shifts(
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    issues: list[BrickExportFidelityIssue] = []

    for stair in sorted(scene.stairs, key=lambda item: item.id):
        start_shift, end_shift = _safe_stair_endpoint_shifts(
            stair,
            scene,
            platform_shifts,
            origin_x=origin_x,
            origin_y=origin_y,
            studs_per_meter=studs_per_meter,
        )
        for endpoint_name, point, endpoint_shift in (
            ("start", stair.start, start_shift),
            ("end", stair.end, end_shift),
        ):
            x, y = _endpoint_raster(
                point,
                endpoint_shift,
                origin_x=origin_x,
                origin_y=origin_y,
                studs_per_meter=studs_per_meter,
            )

            platform = _connected_platform(point, scene)
            if platform is not None:
                if not _point_inside_platform_raster(
                    x,
                    y,
                    platform,
                    platform_shifts.get(platform.id, (0, 0)),
                    origin_x=origin_x,
                    origin_y=origin_y,
                    studs_per_meter=studs_per_meter,
                ):
                    issues.append(
                        BrickExportFidelityIssue(
                            code="lego_stair_platform_contact_not_preserved",
                            severity="warning",
                            object_id=stair.id,
                            message=(
                                f"ArchitecturalScene connects stair {stair.id!r} {endpoint_name} to platform "
                                f"{platform.id!r}, but the final LEGO endpoint falls outside that platform raster. "
                                "The conservative relation solver did not invent a bend or platform movement."
                            ),
                        )
                    )
                continue

            # Match BH-112 interpretation priority: a grounded endpoint is not also
            # treated as a direct building-boundary anchor merely because it lies
            # inside the Scene boundary tolerance.
            if point.z <= base.CONNECTIVITY_TOLERANCE_M:
                continue

            connection = _connected_volume_boundary(point, scene)
            if connection is None:
                continue
            volume, facade = connection
            axis, target = _volume_boundary_target(
                volume,
                facade,
                origin_x=origin_x,
                origin_y=origin_y,
                studs_per_meter=studs_per_meter,
            )
            actual = x if axis == "x" else y
            if actual == target:
                continue
            issues.append(
                BrickExportFidelityIssue(
                    code="lego_stair_volume_contact_not_preserved",
                    severity="warning",
                    object_id=stair.id,
                    message=(
                        f"ArchitecturalScene connects stair {stair.id!r} {endpoint_name} to volume "
                        f"{volume.id!r} {facade.value} boundary, but its final LEGO {axis.upper()} coordinate "
                        f"is {actual} instead of boundary coordinate {target}. The conservative relation solver "
                        "kept the architectural run straight rather than inventing a bend or inversion."
                    ),
                )
            )

    return issues
