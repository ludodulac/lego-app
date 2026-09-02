"""Compact generated chimney course cells into structural canonical bricks.

The Scene chimney renderer first establishes the selected LEGO footprint and emits
one 1x1 cell per occupied stud/course. This layer only exact-covers those emitted
cells with larger placement-approved orthogonal bricks. It cannot change the
selected footprint, fill a skipped collision cell, alter height, or invent caps,
flues or material semantics.
"""
from __future__ import annotations

from collections import defaultdict

from brickhouse.scene.models import ArchitecturalScene

from .brick_model import BrickModel, BrickModelPart

_CANDIDATE_SHAPES: tuple[tuple[int, int, str, int], ...] = (
    (2, 10, "BRICK_2X10", 0), (10, 2, "BRICK_2X10", 1),
    (2, 8, "BRICK_2X8", 0), (8, 2, "BRICK_2X8", 1),
    (2, 6, "BRICK_2X6", 0), (6, 2, "BRICK_2X6", 1),
    (2, 4, "BRICK_2X4", 0), (4, 2, "BRICK_2X4", 1),
    (2, 3, "BRICK_2X3", 0), (3, 2, "BRICK_2X3", 1),
    (2, 2, "BRICK_2X2", 0),
    (1, 8, "BRICK_1X8", 0), (8, 1, "BRICK_1X8", 1),
    (1, 6, "BRICK_1X6", 0), (6, 1, "BRICK_1X6", 1),
    (1, 4, "BRICK_1X4", 0), (4, 1, "BRICK_1X4", 1),
    (1, 3, "BRICK_1X3", 0), (3, 1, "BRICK_1X3", 1),
    (1, 2, "BRICK_1X2", 0), (2, 1, "BRICK_1X2", 1),
    (1, 1, "BRICK_1X1", 0),
)


def _chimney_id(part: BrickModelPart, scene: ArchitecturalScene) -> str | None:
    placement = part.placement_id
    if placement.endswith(":solution"):
        return None
    for chimney in scene.chimneys:
        if placement.startswith(f"scene-chimney:{chimney.id}:"):
            return chimney.id
    return None


def _cells(x: int, y: int, width: int, depth: int) -> set[tuple[int, int]]:
    return {
        (x + dx, y + dy)
        for dx in range(width)
        for dy in range(depth)
    }


def _tile_course(
    source_parts: list[BrickModelPart],
    *,
    chimney_id: str,
) -> list[BrickModelPart]:
    remaining = {(part.x_studs, part.y_studs) for part in source_parts}
    by_cell = {(part.x_studs, part.y_studs): part for part in source_parts}
    result: list[BrickModelPart] = []

    while remaining:
        x, y = min(remaining, key=lambda cell: (cell[1], cell[0]))
        chosen = None
        for width, depth, part_id, rotation in _CANDIDATE_SHAPES:
            occupied = _cells(x, y, width, depth)
            if occupied <= remaining:
                chosen = part_id, rotation, occupied
                break
        assert chosen is not None  # BRICK_1X1 is the exact-cover fallback.
        part_id, rotation, occupied = chosen
        source = by_cell[(x, y)]
        result.append(source.model_copy(update={
            # Source placement ids are globally unique. Deriving the solution id
            # from the retained anchor cell prevents cross-pass/cross-group clashes.
            "placement_id": f"{source.placement_id}:solution",
            "part_id": part_id,
            "rotation_quarter_turns": rotation,
            "x_studs": x,
            "y_studs": y,
        }))
        remaining.difference_update(occupied)

    return result


def compact_scene_chimney_courses(
    model: BrickModel,
    scene: ArchitecturalScene,
) -> BrickModel:
    """Exact-cover generated 1x1 chimney cells independently per Z course."""
    groups: dict[tuple, list[BrickModelPart]] = defaultdict(list)
    retained: list[BrickModelPart] = []

    for part in model.parts:
        chimney_id = _chimney_id(part, scene)
        if chimney_id is None or part.part_id != "BRICK_1X1":
            retained.append(part)
            continue
        key = (
            chimney_id,
            part.z_plates,
            part.facade,
            part.category,
            part.semantic_color,
        )
        groups[key].append(part)

    if not groups:
        return model

    compacted: list[BrickModelPart] = []
    for key in sorted(groups, key=lambda item: (item[0], item[1])):
        chimney_id, *_ = key
        compacted.extend(_tile_course(groups[key], chimney_id=chimney_id))

    return model.model_copy(update={"parts": [*retained, *compacted]})
