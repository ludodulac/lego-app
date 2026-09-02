"""Compact evidence-backed platform railings into structural LEGO runs.

ArchitecturalScene has already decided which platform edge is an open railing and
which cells are access openings. This layer only replaces the generated 1x1
rail-top cells with the longest currently placement-approved canonical 1xN
bricks that cover exactly the same cells. It never bridges a missing/access cell,
adds a railing edge, or changes posts/supports.
"""
from __future__ import annotations

from collections import defaultdict

from brickhouse.scene.models import ArchitecturalScene

from .brick_model import BrickModel, BrickModelPart

_RAIL_SPANS: tuple[tuple[int, str], ...] = (
    (8, "BRICK_1X8"),
    (6, "BRICK_1X6"),
    (4, "BRICK_1X4"),
    (3, "BRICK_1X3"),
    (2, "BRICK_1X2"),
    (1, "BRICK_1X1"),
)
_EDGE_NAMES = ("x_min", "x_max", "y_min", "y_max")


def _rail_identity(part: BrickModelPart, scene: ArchitecturalScene):
    placement = part.placement_id
    for platform in scene.platforms:
        for edge_name in _EDGE_NAMES:
            prefix = f"scene-platform:{platform.id}:{edge_name}:rail-top:"
            if placement.startswith(prefix):
                return platform.id, edge_name
    return None


def _axis_for_edge(edge_name: str) -> str:
    return "y" if edge_name.startswith("x_") else "x"


def _coordinate(part: BrickModelPart, axis: str) -> int:
    return part.y_studs if axis == "y" else part.x_studs


def _fixed_coordinate(part: BrickModelPart, axis: str) -> int:
    return part.x_studs if axis == "y" else part.y_studs


def _contiguous_runs(parts: list[BrickModelPart], axis: str) -> list[list[BrickModelPart]]:
    ordered = sorted(parts, key=lambda part: _coordinate(part, axis))
    if not ordered:
        return []
    runs: list[list[BrickModelPart]] = [[ordered[0]]]
    for part in ordered[1:]:
        if _coordinate(part, axis) == _coordinate(runs[-1][-1], axis) + 1:
            runs[-1].append(part)
        else:
            runs.append([part])
    return runs


def _tile_run(
    run: list[BrickModelPart],
    *,
    platform_id: str,
    edge_name: str,
    axis: str,
    serial_start: int,
) -> tuple[list[BrickModelPart], int]:
    result: list[BrickModelPart] = []
    cursor = 0
    serial = serial_start
    while cursor < len(run):
        remaining = len(run) - cursor
        span, part_id = next((span, part_id) for span, part_id in _RAIL_SPANS if span <= remaining)
        source = run[cursor]
        result.append(source.model_copy(update={
            "placement_id": f"scene-platform:{platform_id}:{edge_name}:rail-top-solution:{serial:05d}",
            "part_id": part_id,
            "rotation_quarter_turns": 0 if axis == "y" or span == 1 else 1,
        }))
        serial += 1
        cursor += span
    return result, serial


def compact_scene_platform_railings(model: BrickModel, scene: ArchitecturalScene) -> BrickModel:
    """Return a model with exact-cell open-railing top runs compacted.

    Groups are split by platform edge, height, facade, material category and fixed
    coordinate. Missing source cells therefore remain hard gaps. Only source
    ``BRICK_1X1`` rail-top cells are eligible; an already specialized rail part is
    left untouched rather than reinterpreted.
    """
    groups: dict[tuple, list[BrickModelPart]] = defaultdict(list)
    retained: list[BrickModelPart] = []

    for part in model.parts:
        identity = _rail_identity(part, scene)
        if identity is None or part.part_id != "BRICK_1X1":
            retained.append(part)
            continue
        platform_id, edge_name = identity
        axis = _axis_for_edge(edge_name)
        key = (
            platform_id,
            edge_name,
            part.z_plates,
            part.facade,
            part.category,
            _fixed_coordinate(part, axis),
        )
        groups[key].append(part)

    if not groups:
        return model

    compacted: list[BrickModelPart] = []
    serial = 1
    for key in sorted(groups, key=lambda item: (item[0], item[1], item[2], item[5])):
        platform_id, edge_name, *_ = key
        axis = _axis_for_edge(edge_name)
        for run in _contiguous_runs(groups[key], axis):
            tiled, serial = _tile_run(
                run,
                platform_id=platform_id,
                edge_name=edge_name,
                axis=axis,
                serial_start=serial,
            )
            compacted.extend(tiled)

    # Preserve deterministic global ordering: existing non-rail parts first in
    # their generated order, then stable compacted railing solutions.
    return model.model_copy(update={"parts": [*retained, *compacted]})
