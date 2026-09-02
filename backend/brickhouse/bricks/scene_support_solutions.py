"""Compact declared platform support cells into structural LEGO brick courses.

ArchitecturalScene has already decided which metric SupportPost objects exist and
``scene_architecture`` has quantized those objects into exact occupied LEGO cells.
This layer only replaces generated 1x1 support cells with larger canonical bricks
that cover the *same* cells at the *same* heights. It never adds, moves, widens,
extends or joins supports, and it never infers missing beams or bracing.
"""
from __future__ import annotations

from collections import defaultdict
import re

from brickhouse.scene.models import ArchitecturalScene

from .brick_model import BrickModel, BrickModelPart

_SUPPORT_TOKEN = re.compile(r"^support(?P<index>[1-9][0-9]*)$")

# Canonical M0 bricks are placement-approved. Dimensions below are expressed in
# model X/Y studs for rotation=0; rotation=1 swaps them. Order is deliberately
# largest-area first so a rectangular structural post becomes a small number of
# coherent courses rather than a field of 1x1 cells.
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


def _support_identity(
    part: BrickModelPart,
    scene: ArchitecturalScene,
) -> tuple[str, str] | None:
    """Return (platform_id, support_id) only for generated support-cell parts."""
    placement = part.placement_id
    for platform in scene.platforms:
        prefix = f"scene-platform:{platform.id}:"
        if not placement.startswith(prefix):
            continue
        tail = placement[len(prefix):]
        token = tail.split(":", 1)[0]
        match = _SUPPORT_TOKEN.match(token)
        if match is None:
            return None
        support_index = int(match.group("index")) - 1
        if support_index >= len(platform.supports):
            return None
        return platform.id, platform.supports[support_index].id
    return None


def _shape_cells(x: int, y: int, width: int, depth: int) -> set[tuple[int, int]]:
    return {
        (x + dx, y + dy)
        for dx in range(width)
        for dy in range(depth)
    }


def _tile_course(
    source_parts: list[BrickModelPart],
    *,
    platform_id: str,
    support_id: str,
    serial_start: int,
) -> tuple[list[BrickModelPart], int]:
    """Exact-cover one support course with placement-approved canonical bricks."""
    remaining = {(part.x_studs, part.y_studs) for part in source_parts}
    by_cell = {(part.x_studs, part.y_studs): part for part in source_parts}
    result: list[BrickModelPart] = []
    serial = serial_start

    while remaining:
        # Stable lower-left sweep. A candidate is accepted only when every stud it
        # covers was occupied by the source 1x1 representation.
        x, y = min(remaining, key=lambda cell: (cell[1], cell[0]))
        chosen = None
        for width, depth, part_id, rotation in _CANDIDATE_SHAPES:
            cells = _shape_cells(x, y, width, depth)
            if cells <= remaining:
                chosen = width, depth, part_id, rotation, cells
                break
        assert chosen is not None  # 1x1 is always the final exact-cover fallback.
        _, _, part_id, rotation, cells = chosen
        source = by_cell[(x, y)]
        result.append(source.model_copy(update={
            "placement_id": (
                f"scene-platform:{platform_id}:support-solution:{support_id}:"
                f"{source.z_plates:04d}:{serial:05d}"
            ),
            "part_id": part_id,
            "rotation_quarter_turns": rotation,
            "x_studs": x,
            "y_studs": y,
        }))
        remaining.difference_update(cells)
        serial += 1

    return result, serial


def compact_scene_platform_supports(
    model: BrickModel,
    scene: ArchitecturalScene,
) -> BrickModel:
    """Replace source 1x1 support cells by exact-cell structural brick courses.

    Grouping includes platform/support identity, Z, facade and material category,
    so different supports, heights or semantic materials can never be joined by a
    larger brick. Non-1x1 or already-specialized support parts are retained.
    """
    groups: dict[tuple, list[BrickModelPart]] = defaultdict(list)
    retained: list[BrickModelPart] = []

    for part in model.parts:
        identity = _support_identity(part, scene)
        if identity is None or part.part_id != "BRICK_1X1":
            retained.append(part)
            continue
        platform_id, support_id = identity
        key = (
            platform_id,
            support_id,
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
    for key in sorted(groups, key=lambda item: (item[0], item[1], item[2])):
        platform_id, support_id, *_ = key
        tiled, serial = _tile_course(
            groups[key],
            platform_id=platform_id,
            support_id=support_id,
            serial_start=serial,
        )
        compacted.extend(tiled)

    return model.model_copy(update={"parts": [*retained, *compacted]})
