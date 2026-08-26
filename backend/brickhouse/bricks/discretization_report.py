"""Helpers for measuring metric-to-LEGO grid loss without changing geometry."""

from __future__ import annotations

from brickhouse.building.models import BuildingModel
from brickhouse.geometry import generate_building_geometry

from .building_layout import BuildingDiscretizationQuality, generate_building_brick_shell
from .scaling import COURSES_PER_STUD_RATIO


def build_discretization_quality(
    building: BuildingModel,
    *,
    front_width_studs: int,
) -> list[BuildingDiscretizationQuality]:
    """Return one deterministic snap-error report per modeled volume."""
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")
    geometry = generate_building_geometry(building)
    primary = building.volumes[0]
    studs_per_meter = front_width_studs / primary.width
    results: list[BuildingDiscretizationQuality] = []

    for volume in building.volumes:
        walls = [wall for wall in geometry.walls if wall.volume_id == volume.id]
        roof_planes = [plane for plane in geometry.roof_planes if plane.volume_id == volume.id]
        subgeometry = geometry.model_copy(update={"walls": walls, "roof_planes": roof_planes})
        shell = generate_building_brick_shell(subgeometry, studs_per_meter=studs_per_meter)
        if shell.discretization_quality is not None:
            results.append(shell.discretization_quality)

    return results
