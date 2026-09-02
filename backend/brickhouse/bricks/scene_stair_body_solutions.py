"""Compact generated masonry stair body cells without changing occupied volume.

The Scene renderer has already decided the evidence-backed stepped volume and
emitted one canonical 1x1 brick per occupied cell/course. This layer exact-covers
those cells with larger placement-approved bricks. It never fills a missing cell,
changes a tread, joins separate stairs or alters ArchitecturalScene geometry.
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


def _stair_id_for_body(part: BrickModelPart, scene: ArchitecturalScene) -> str | None:
    placement = part.placement_id
    for stair in scene.stairs:
        if placement.startswith(f"scene-stair:{stair.id}:body:"):
            return stair.id
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
    stair_id: str,
    serial_start: int,
) -> tuple[list[BrickModelPart], int]:
    remaining = {(part.x_studs, part.y_studs) for part in source_parts}
    by_cell = {(part.x_studs, part.y_studs): part for part in source_parts}
    result: list[BrickModelPart] = []
    serial = serial_start

    while remaining:
        x, y = min(remaining, key=lambda cell: (cell[1], cell[0]))
        chosen = None
        for width, depth, part_id, rotation in _CANDIDATE_SHAPES:
            occupied = _cells(x, y, width, depth)
            if occupied <= remaining:
                chosen = part_id, rotation, occupied
                break
        assert chosen is not None  # 1x1 is the exact-cover fallback.
        part_id, rotation, occupied = chosen
        source = by_cell[(x, y)]
        result.append(source.model_copy(update={
            # Preserve the historic provenance prefix used by downstream tests.
            "placement_id": f"scene-stair:{stair_id}:body:solution:{source.z_plates:04d}:{serial:05d}",
            "part_id": part_id,
            "rotation_quarter_turns": rotation,
            "x_studs": x,
            "y_studs": y,
        }))
        remaining.difference_update(occupied)
        serial += 1

    return result, serial


def compact_scene_stair_bodies(
    model: BrickModel,
    scene: ArchitecturalScene,
) -> BrickModel:
    """Exact-cover generated masonry stair body cells by stair and Z course."""
    groups: dict[tuple, list[BrickModelPart]] = defaultdict(list)
    retained: list[BrickModelPart] = []

    for part in model.parts:
        stair_id = _stair_id_for_body(part, scene)
        if stair_id is None or part.part_id != "BRICK_1X1":
            retained.append(part)
            continue
        key = (
            stair_id,
            part.z_plates,
            part.facade,
            part.category,
            part.semantic_color,
        )
        groups[key].append(part)

    if not groups:
        return model

    compacted: list[BrickModelPart] = []
    serial = 1
    for key in sorted(groups, key=lambda item: (item[0], item[1])):
        stair_id, *_ = key
        tiled, serial = _tile_course(
            groups[key],
            stair_id=stair_id,
            serial_start=serial,
        )
        compacted.extend(tiled)

    return model.model_copy(update={"parts": [*retained, *compacted]})
