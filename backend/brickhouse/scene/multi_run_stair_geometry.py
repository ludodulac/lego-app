"""Deterministic continuity facts for multi-run architectural stairs.

Survey topology is semantic truth; this module only checks whether already-metric
Scene ``StairRun`` components can realize that topology. It never invents a
landing, a tread count, an angle, or a missing coordinate.
"""
from __future__ import annotations

from math import hypot

from pydantic import BaseModel, Field

from brickhouse.survey import ArchitecturalSurvey, Certainty, analyze_survey_stair_topology

from .models import CONNECTIVITY_TOLERANCE_M, EPSILON
from .wall_profile_scene import ArchitecturalScene


_DIRECTION_EPSILON = 1e-6


class StairRunJunction(BaseModel):
    first_run_id: str
    second_run_id: str
    first_endpoint: str
    second_endpoint: str
    horizontal_gap: float = Field(ge=0)
    vertical_gap: float = Field(ge=0)
    direction_change: bool | None = None


class MultiRunStairGeometryFacts(BaseModel):
    observation_id: str
    component_run_ids: list[str]
    all_components_present: bool
    connected: bool | None = None
    spanning_path_exists: bool | None = None
    direction_change_realized: bool | None = None
    degenerate_run_ids: list[str] = Field(default_factory=list)
    junctions: list[StairRunJunction] = Field(default_factory=list)


class MultiRunStairGeometryReport(BaseModel):
    facts: list[MultiRunStairGeometryFacts] = Field(default_factory=list)


def _xy_direction(stair) -> tuple[float, float] | None:
    dx = stair.end.x - stair.start.x
    dy = stair.end.y - stair.start.y
    length = hypot(dx, dy)
    if length <= EPSILON:
        return None
    return dx / length, dy / length


def _direction_change(first, second) -> bool | None:
    a = _xy_direction(first)
    b = _xy_direction(second)
    if a is None or b is None:
        return None
    # Endpoint serialization may reverse one run. Absolute cross magnitude is
    # orientation-independent: opposite collinear vectors still mean no turn.
    cross = abs(a[0] * b[1] - a[1] * b[0])
    return cross > _DIRECTION_EPSILON


def _junction(first, second) -> StairRunJunction | None:
    best = None
    for first_name, first_point in (("start", first.start), ("end", first.end)):
        for second_name, second_point in (("start", second.start), ("end", second.end)):
            horizontal_gap = hypot(first_point.x - second_point.x, first_point.y - second_point.y)
            vertical_gap = abs(first_point.z - second_point.z)
            key = (max(horizontal_gap, vertical_gap), horizontal_gap + vertical_gap)
            if best is None or key < best[0]:
                best = (key, first_name, second_name, horizontal_gap, vertical_gap)
    assert best is not None
    _, first_name, second_name, horizontal_gap, vertical_gap = best
    if horizontal_gap > CONNECTIVITY_TOLERANCE_M or vertical_gap > CONNECTIVITY_TOLERANCE_M:
        return None
    return StairRunJunction(
        first_run_id=first.id,
        second_run_id=second.id,
        first_endpoint=first_name,
        second_endpoint=second_name,
        horizontal_gap=horizontal_gap,
        vertical_gap=vertical_gap,
        direction_change=_direction_change(first, second),
    )


def _connected(adjacency: dict[str, set[str]]) -> bool:
    if not adjacency:
        return False
    start = next(iter(adjacency))
    seen = {start}
    stack = [start]
    while stack:
        current = stack.pop()
        for neighbor in adjacency[current] - seen:
            seen.add(neighbor)
            stack.append(neighbor)
    return len(seen) == len(adjacency)


def _has_spanning_path(adjacency: dict[str, set[str]]) -> bool:
    """Return whether the component graph can form one continuous stair path.

    Component IDs are not assumed to encode order. We therefore search for any
    path visiting every run once instead of imposing list order that Survey does
    not promise.
    """
    count = len(adjacency)
    if count == 0:
        return False
    if count == 1:
        return True

    def visit(current: str, seen: set[str]) -> bool:
        if len(seen) == count:
            return True
        return any(visit(neighbor, seen | {neighbor}) for neighbor in adjacency[current] - seen)

    return any(visit(start, {start}) for start in adjacency)


def analyze_multi_run_stair_geometry(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> MultiRunStairGeometryReport:
    """Derive multi-run continuity only for certain explicit component systems."""
    scene_stairs = {item.id: item for item in scene.stairs}
    facts: list[MultiRunStairGeometryFacts] = []

    for topology_fact in analyze_survey_stair_topology(survey).facts:
        if topology_fact.certainty is not Certainty.CERTAIN:
            continue
        component_ids = topology_fact.topology.component_run_ids
        if len(component_ids) < 2:
            continue

        missing = [item for item in component_ids if item not in scene_stairs]
        if missing:
            facts.append(MultiRunStairGeometryFacts(
                observation_id=topology_fact.observation_id,
                component_run_ids=list(component_ids),
                all_components_present=False,
            ))
            continue

        stairs = [scene_stairs[item] for item in component_ids]
        degenerate = sorted(item.id for item in stairs if _xy_direction(item) is None)
        adjacency = {item.id: set() for item in stairs}
        junctions: list[StairRunJunction] = []
        for index, first in enumerate(stairs):
            for second in stairs[index + 1:]:
                junction = _junction(first, second)
                if junction is None:
                    continue
                adjacency[first.id].add(second.id)
                adjacency[second.id].add(first.id)
                junctions.append(junction)

        is_connected = _connected(adjacency)
        spanning_path = _has_spanning_path(adjacency) if is_connected else False
        direction_values = [item.direction_change for item in junctions]
        if any(value is True for value in direction_values):
            direction_realized: bool | None = True
        elif any(value is None for value in direction_values) or degenerate:
            direction_realized = None
        else:
            direction_realized = False

        facts.append(MultiRunStairGeometryFacts(
            observation_id=topology_fact.observation_id,
            component_run_ids=list(component_ids),
            all_components_present=True,
            connected=is_connected,
            spanning_path_exists=spanning_path,
            direction_change_realized=direction_realized,
            degenerate_run_ids=degenerate,
            junctions=sorted(junctions, key=lambda item: (item.first_run_id, item.second_run_id)),
        ))

    return MultiRunStairGeometryReport(facts=facts)
