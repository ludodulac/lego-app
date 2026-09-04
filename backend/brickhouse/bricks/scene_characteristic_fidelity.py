"""Fidelity diagnostics for characteristic exterior Scene geometry.

ArchitecturalScene remains immutable.  This module mirrors the renderer's existing
quantization rules and reports how much characteristic platforms, stairs and
chimneys change when represented on the LEGO grid.  It is deliberately diagnostic:
no object is moved or resized here.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, hypot

from brickhouse.scene.models import ArchitecturalScene

from .export import BrickExportFidelityIssue
from .scaling import COURSES_PER_STUD_RATIO
from .scene_architecture import (
    EPSILON,
    _connected_platform_course,
    _course_z,
    _round_half_up,
    _scene_bounds,
)
from .scene_architecture_relations import (
    _platform_representation_shifts,
    _safe_stair_endpoint_shifts,
)
from .scene_chimney_solutions import select_scene_chimney_footprints


MATERIAL_CHARACTERISTIC_ERROR = 0.20
SEVERE_CHARACTERISTIC_ERROR = 0.35
MATERIAL_POSITION_ERROR = 0.03
SEVERE_POSITION_ERROR = 0.06


@dataclass(frozen=True)
class CharacteristicDistortion:
    object_id: str
    kind: str
    worst_relative_error: float
    position_error_fraction: float = 0.0
    details: str = ""


def _relative_error(target: float, represented: float) -> float:
    if target <= EPSILON:
        return 0.0 if abs(represented) <= EPSILON else 1.0
    return abs(represented - target) / target


def _severity(metric: CharacteristicDistortion) -> str | None:
    if (
        metric.worst_relative_error >= SEVERE_CHARACTERISTIC_ERROR
        or metric.position_error_fraction >= SEVERE_POSITION_ERROR
    ):
        return "blocker"
    if (
        metric.worst_relative_error >= MATERIAL_CHARACTERISTIC_ERROR
        or metric.position_error_fraction >= MATERIAL_POSITION_ERROR
    ):
        return "warning"
    if metric.worst_relative_error > 0.01 or metric.position_error_fraction > 0.01:
        return "info"
    return None


def characteristic_distortions(
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> tuple[CharacteristicDistortion, ...]:
    """Measure final-grid distortion with the same quantizers as the renderer."""
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")
    main = scene.volumes[0]
    if main.width.value is None:
        return ()

    studs_per_meter = front_width_studs / main.width.value
    plates_per_meter = studs_per_meter * COURSES_PER_STUD_RATIO * 3
    origin_x, origin_y, origin_z = _scene_bounds(scene)
    platform_shifts = _platform_representation_shifts(
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=studs_per_meter,
    )
    metrics: list[CharacteristicDistortion] = []

    for platform in scene.platforms:
        target_width = platform.width * studs_per_meter
        target_depth = platform.depth * studs_per_meter
        raster_width = max(1, ceil(target_width - EPSILON))
        raster_depth = max(1, ceil(target_depth - EPSILON))
        width_error = _relative_error(target_width, raster_width)
        depth_error = _relative_error(target_depth, raster_depth)
        metrics.append(
            CharacteristicDistortion(
                object_id=platform.id,
                kind="platform",
                worst_relative_error=max(width_error, depth_error),
                details=(
                    f"width {target_width:.3f}->{raster_width} studs; "
                    f"depth {target_depth:.3f}->{raster_depth} studs"
                ),
            )
        )

    for stair in scene.stairs:
        start_shift, end_shift = _safe_stair_endpoint_shifts(
            stair,
            scene,
            platform_shifts,
            origin_x=origin_x,
            origin_y=origin_y,
            studs_per_meter=studs_per_meter,
        )
        sx = _round_half_up((stair.start.x - origin_x) * studs_per_meter) + start_shift[0]
        sy = _round_half_up((stair.start.y - origin_y) * studs_per_meter) + start_shift[1]
        ex = _round_half_up((stair.end.x - origin_x) * studs_per_meter) + end_shift[0]
        ey = _round_half_up((stair.end.y - origin_y) * studs_per_meter) + end_shift[1]
        target_run = max(
            abs(stair.end.x - stair.start.x),
            abs(stair.end.y - stair.start.y),
        ) * studs_per_meter
        raster_run = max(abs(ex - sx), abs(ey - sy))

        start_z = _connected_platform_course(
            stair.start,
            scene,
            origin_z=origin_z,
            plates_per_meter=plates_per_meter,
        )
        if start_z is None:
            start_z = _course_z(stair.start.z, origin_z, plates_per_meter)
        end_z = _connected_platform_course(
            stair.end,
            scene,
            origin_z=origin_z,
            plates_per_meter=plates_per_meter,
        )
        if end_z is None:
            end_z = _course_z(stair.end.z, origin_z, plates_per_meter)
        target_rise = abs(stair.end.z - stair.start.z) * plates_per_meter
        raster_rise = abs(end_z - start_z)
        target_width = stair.width * studs_per_meter
        raster_width = max(1, _round_half_up(target_width))
        run_error = _relative_error(target_run, raster_run)
        rise_error = _relative_error(target_rise, raster_rise)
        width_error = _relative_error(target_width, raster_width)
        metrics.append(
            CharacteristicDistortion(
                object_id=stair.id,
                kind="stair",
                worst_relative_error=max(run_error, rise_error, width_error),
                details=(
                    f"run {target_run:.3f}->{raster_run} studs; "
                    f"rise {target_rise:.3f}->{raster_rise} plates; "
                    f"width {target_width:.3f}->{raster_width} studs"
                ),
            )
        )

    solutions = {
        solution.chimney_id: solution
        for solution in select_scene_chimney_footprints(
            scene,
            front_width_studs=front_width_studs,
        )
    }
    for chimney in scene.chimneys:
        solution = solutions[chimney.id]
        x0 = _round_half_up((chimney.position.x - origin_x) * studs_per_meter)
        y0 = _round_half_up((chimney.position.y - origin_y) * studs_per_meter)
        target_center_x = (
            chimney.position.x + chimney.width / 2 - origin_x
        ) * studs_per_meter
        target_center_y = (
            chimney.position.y + chimney.depth / 2 - origin_y
        ) * studs_per_meter
        raster_center_x = x0 + solution.width_studs / 2
        raster_center_y = y0 + solution.depth_studs / 2
        center_shift = hypot(
            raster_center_x - target_center_x,
            raster_center_y - target_center_y,
        )
        width_error = _relative_error(
            solution.target_width_studs,
            solution.width_studs,
        )
        depth_error = _relative_error(
            solution.target_depth_studs,
            solution.depth_studs,
        )
        metrics.append(
            CharacteristicDistortion(
                object_id=chimney.id,
                kind="chimney",
                worst_relative_error=max(width_error, depth_error),
                position_error_fraction=center_shift / front_width_studs,
                details=(
                    f"footprint {solution.target_width_studs:.3f}x"
                    f"{solution.target_depth_studs:.3f}->{solution.width_studs}x"
                    f"{solution.depth_studs} studs; center shift {center_shift:.3f} studs"
                ),
            )
        )

    return tuple(metrics)


def characteristic_fidelity_issues(
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> list[BrickExportFidelityIssue]:
    """Convert characteristic distortion metrics into traceable export issues."""
    issues: list[BrickExportFidelityIssue] = []
    for metric in characteristic_distortions(
        scene,
        front_width_studs=front_width_studs,
    ):
        severity = _severity(metric)
        if severity is None:
            continue
        issues.append(
            BrickExportFidelityIssue(
                code=f"lego_{metric.kind}_proportion_distortion",
                severity=severity,
                object_id=metric.object_id,
                message=(
                    f"ArchitecturalScene {metric.kind} {metric.object_id!r} remains unchanged; "
                    f"its LEGO representation has {metric.worst_relative_error * 100:.1f}% "
                    f"worst proportional distortion and {metric.position_error_fraction * 100:.1f}% "
                    f"front-width-normalized position drift ({metric.details})."
                ),
            )
        )
    return issues
