"""Compact evidence-backed stair tread cells into coherent LEGO runs.

ArchitecturalScene remains authoritative. ``scene_architecture`` first quantizes a
StairRun into exact tread cells. This module only replaces contiguous generated
1x1 tread cells across the declared stair width with placement-approved canonical
1xN bricks that cover the same cells. It never changes run position, elevation,
width, edge treatment, masonry body fill, or missing-cell gaps.
"""
from __future__ import annotations

from collections import defaultdict

from brickhouse.scene.models import ArchitecturalScene, StairRun

from .brick_model import BrickModel, BrickModelPart

_TREAD_SPANS: tuple[tuple[int, str], ...] = (
    (8, "BRICK_1X8"),
    (6, "BRICK_1X6"),
    (4, "BRICK_1X4"),
    (3, "BRICK_1X3"),
    (2, "BRICK_1X2"),
    (1, "BRICK_1X1"),
)


def _stair_for_tread(part: BrickModelPart, scene: ArchitecturalScene) -> StairRun | None:
    placement = part.placement_id
    for stair in scene.stairs:
        if placement.startswith(f"scene-stair:{stair.id}:tread:"):
            return stair
    return None


def _width_axis(stair: StairRun) -> str:
    dx = abs(stair.end.x - stair.start.x)
    dy = abs(stair.end.y - stair.start.y)
    # scene_architecture uses X as the run axis on ties, so width is Y.
    return "y" if dx >= dy else "x"


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
    stair_id: str,
    axis: str,
    serial_start: int,
) -> tuple[list[BrickModelPart], int]:
    result: list[BrickModelPart] = []
    cursor = 0
    serial = serial_start
    while cursor < len(run):
        remaining = len(run) - cursor
        span, part_id = next(
            (span, part_id) for span, part_id in _TREAD_SPANS if span <= remaining
        )
        source = run[cursor]
        result.append(source.model_copy(update={
            "placement_id": f"scene-stair:{stair_id}:tread-solution:{serial:05d}",
            "part_id": part_id,
            "rotation_quarter_turns": 0 if axis == "y" or span == 1 else 1,
        }))
        cursor += span
        serial += 1
    return result, serial


def compact_scene_stair_treads(
    model: BrickModel,
    scene: ArchitecturalScene,
) -> BrickModel:
    """Exact-cover generated tread-width cells with canonical 1xN bricks.

    Groups are separated by stair identity, tread Z, run-axis coordinate, facade,
    material category and semantic color. Different steps therefore cannot merge,
    even when they happen to share a height after LEGO quantization. Missing cells
    split a group into independent contiguous runs and remain hard gaps.
    """
    groups: dict[tuple, list[BrickModelPart]] = defaultdict(list)
    retained: list[BrickModelPart] = []

    for part in model.parts:
        stair = _stair_for_tread(part, scene)
        if stair is None or part.part_id != "BRICK_1X1":
            retained.append(part)
            continue
        axis = _width_axis(stair)
        key = (
            stair.id,
            axis,
            part.z_plates,
            _fixed_coordinate(part, axis),
            part.facade,
            part.category,
            part.semantic_color,
        )
        groups[key].append(part)

    if not groups:
        return model

    compacted: list[BrickModelPart] = []
    serial = 1
    for key in sorted(groups, key=lambda item: (item[0], item[2], item[3])):
        stair_id, axis, *_ = key
        for run in _contiguous_runs(groups[key], axis):
            tiled, serial = _tile_run(
                run,
                stair_id=stair_id,
                axis=axis,
                serial_start=serial,
            )
            compacted.extend(tiled)

    return model.model_copy(update={"parts": [*retained, *compacted]})
