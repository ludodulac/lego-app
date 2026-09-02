"""Select LEGO chimney footprints by architectural proportion fidelity.

ArchitecturalScene metric geometry is immutable. This module chooses only the
integer stud footprint used by the LEGO representation, avoiding the systematic
oversizing caused by independently ceiling width and depth. Candidate footprints
stay local to the metric target and are scored by dimensional, aspect-ratio and
area fidelity.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, floor, log

from brickhouse.scene.models import ArchitecturalScene, Chimney


@dataclass(frozen=True)
class ChimneyFootprintSolution:
    chimney_id: str
    target_width_studs: float
    target_depth_studs: float
    width_studs: int
    depth_studs: int
    dimensional_error: float
    aspect_ratio_error: float
    area_error: float
    score: float

    @property
    def geometry_changed(self) -> bool:
        return (
            abs(self.width_studs - self.target_width_studs) > 1e-9
            or abs(self.depth_studs - self.target_depth_studs) > 1e-9
        )


def _candidate_axis(target: float) -> tuple[int, ...]:
    lower = max(1, floor(target) - 1)
    upper = max(1, ceil(target) + 1)
    return tuple(range(lower, upper + 1))


def _score(target_width: float, target_depth: float, width: int, depth: int) -> tuple[float, float, float, float]:
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


def select_chimney_footprint(chimney: Chimney, *, studs_per_meter: float) -> ChimneyFootprintSolution:
    """Return the best nearby integer footprint for one metric chimney.

    The search is intentionally small: only integer sizes around the target are
    considered, with a one-stud safety neighborhood on either side. This is a
    representation choice, not a modification of the source chimney geometry.
    """
    if studs_per_meter <= 0:
        raise ValueError("studs_per_meter must be positive")

    target_width = chimney.width * studs_per_meter
    target_depth = chimney.depth * studs_per_meter
    ranked: list[tuple[tuple[float, float, float, float, int, int, int], ChimneyFootprintSolution]] = []

    for width in _candidate_axis(target_width):
        for depth in _candidate_axis(target_depth):
            score, dimensional_error, aspect_ratio_error, area_error = _score(
                target_width,
                target_depth,
                width,
                depth,
            )
            solution = ChimneyFootprintSolution(
                chimney_id=chimney.id,
                target_width_studs=target_width,
                target_depth_studs=target_depth,
                width_studs=width,
                depth_studs=depth,
                dimensional_error=dimensional_error,
                aspect_ratio_error=aspect_ratio_error,
                area_error=area_error,
                score=score,
            )
            # Stable tie-breaking favors lower error, then the smaller footprint
            # rather than recreating the old systematic outward-rounding bias.
            key = (
                round(score, 12),
                round(aspect_ratio_error, 12),
                round(dimensional_error, 12),
                round(area_error, 12),
                width * depth,
                width,
                depth,
            )
            ranked.append((key, solution))

    return min(ranked, key=lambda item: item[0])[1]


def select_scene_chimney_footprints(
    scene: ArchitecturalScene,
    *,
    front_width_studs: int,
) -> tuple[ChimneyFootprintSolution, ...]:
    """Select footprint solutions for every explicitly declared Scene chimney."""
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")
    if not scene.chimneys:
        return ()
    main = scene.volumes[0]
    if main.width.value is None:
        return ()
    studs_per_meter = front_width_studs / main.width.value
    return tuple(
        select_chimney_footprint(chimney, studs_per_meter=studs_per_meter)
        for chimney in scene.chimneys
    )
