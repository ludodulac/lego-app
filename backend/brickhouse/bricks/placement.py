"""Deterministic brick placement for simple rectangular walls."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.bricks.catalog import create_m0_brick_catalog


class BrickPlacement(BaseModel):
    brick_id: str
    x_studs: int = Field(ge=0)
    y_studs: int = Field(default=0, ge=0)
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3]


class WallBrickLayout(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    wall_width_studs: int = Field(gt=0)
    wall_height_bricks: int = Field(gt=0)
    wall_thickness_studs: Literal[1] = 1
    placements: list[BrickPlacement]


_CANONICAL_SPANNING_BRICKS: tuple[tuple[int, str], ...] = (
    (8, "BRICK_1X8"),
    (6, "BRICK_1X6"),
    (4, "BRICK_1X4"),
    (3, "BRICK_1X3"),
    (2, "BRICK_1X2"),
    (1, "BRICK_1X1"),
)
_BRICK_ID_BY_SPAN = dict(_CANONICAL_SPANNING_BRICKS)


def _internal_joints(composition: tuple[int, ...]) -> frozenset[int]:
    joints: set[int] = set()
    x = 0
    for span in composition[:-1]:
        x += span
        joints.add(x)
    return frozenset(joints)


def _choose_course_composition(
    width_studs: int,
    previous_joints: frozenset[int],
) -> tuple[int, ...]:
    """Find the best exact composition without enumerating all compositions."""

    @lru_cache(maxsize=None)
    def solve(x_studs: int) -> tuple[int, int, tuple[int, ...]] | None:
        if x_studs == width_studs:
            return 0, 0, ()

        best: tuple[int, int, tuple[int, ...]] | None = None
        for span, _ in _CANONICAL_SPANNING_BRICKS:
            end = x_studs + span
            if end > width_studs:
                continue

            tail = solve(end)
            if tail is None:
                continue

            tail_overlap, tail_count, tail_spans = tail
            boundary_overlap = 1 if end < width_studs and end in previous_joints else 0
            candidate = (
                boundary_overlap + tail_overlap,
                1 + tail_count,
                (span, *tail_spans),
            )

            if best is None:
                best = candidate
                continue

            candidate_key = (
                candidate[0],
                candidate[1],
                tuple(-value for value in candidate[2]),
            )
            best_key = (
                best[0],
                best[1],
                tuple(-value for value in best[2]),
            )
            if candidate_key < best_key:
                best = candidate

        return best

    result = solve(0)
    if result is None:
        raise RuntimeError(f"no exact canonical brick composition for width {width_studs}")
    return result[2]


def generate_simple_wall_layout(width_studs: int, height_bricks: int) -> WallBrickLayout:
    """Fill a 1-stud-thick wall with exact coverage and stagger adjacent joints.

    The first course minimizes brick count and then prefers larger pieces.
    Each later course first minimizes internal joints shared with the previous
    course, then brick count, then prefers larger pieces deterministically.
    """
    layout = WallBrickLayout(
        wall_width_studs=width_studs,
        wall_height_bricks=height_bricks,
        placements=[],
    )
    catalog = create_m0_brick_catalog()
    previous_joints: frozenset[int] = frozenset()

    for course in range(height_bricks):
        composition = _choose_course_composition(width_studs, previous_joints)
        x = 0

        for span in composition:
            brick_id = _BRICK_ID_BY_SPAN[span]
            brick = catalog.get(brick_id)
            rotation = 0 if span == 1 else 1
            footprint_x, footprint_y = brick.footprint(rotation)
            if footprint_x != span or footprint_y != 1:
                raise RuntimeError(
                    f"canonical brick {brick_id} does not match wall placement assumptions"
                )

            layout.placements.append(
                BrickPlacement(
                    brick_id=brick_id,
                    x_studs=x,
                    y_studs=0,
                    z_plates=course * 3,
                    rotation_quarter_turns=rotation,
                )
            )
            x += span

        previous_joints = _internal_joints(composition)

    return layout
