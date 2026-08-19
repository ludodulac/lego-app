"""Deterministic brick placement for rectangular walls with grid-aligned openings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.bricks.catalog import create_m0_brick_catalog


class BrickPlacement(BaseModel):
    brick_id: str
    x_studs: int = Field(ge=0)
    y_studs: int = Field(default=0, ge=0)
    z_plates: int = Field(ge=0)
    rotation_quarter_turns: Literal[0, 1, 2, 3]


class WallOpeningGrid(BaseModel):
    id: str
    x_studs: int = Field(ge=0)
    z_bricks: int = Field(ge=0)
    width_studs: int = Field(gt=0)
    height_bricks: int = Field(gt=0)

    @property
    def x_end(self) -> int:
        return self.x_studs + self.width_studs

    @property
    def z_end(self) -> int:
        return self.z_bricks + self.height_bricks


class WallBrickLayout(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    wall_width_studs: int = Field(gt=0)
    wall_height_bricks: int = Field(gt=0)
    wall_thickness_studs: Literal[1] = 1
    openings: list[WallOpeningGrid] = Field(default_factory=list)
    placements: list[BrickPlacement]

    @model_validator(mode="after")
    def validate_openings(self) -> "WallBrickLayout":
        ids = [opening.id for opening in self.openings]
        if len(ids) != len(set(ids)):
            raise ValueError("opening IDs must be unique")

        for opening in self.openings:
            if opening.x_end > self.wall_width_studs:
                raise ValueError(f"opening {opening.id!r} extends past wall horizontally")
            if opening.z_end > self.wall_height_bricks:
                raise ValueError(f"opening {opening.id!r} extends above wall")

        for index, first in enumerate(self.openings):
            for second in self.openings[index + 1 :]:
                horizontal_overlap = first.x_studs < second.x_end and second.x_studs < first.x_end
                vertical_overlap = first.z_bricks < second.z_end and second.z_bricks < first.z_end
                if horizontal_overlap and vertical_overlap:
                    raise ValueError(f"openings {first.id!r} and {second.id!r} overlap")
        return self


_CANONICAL_SPANNING_BRICKS: tuple[tuple[int, str], ...] = (
    (8, "BRICK_1X8"),
    (6, "BRICK_1X6"),
    (4, "BRICK_1X4"),
    (3, "BRICK_1X3"),
    (2, "BRICK_1X2"),
    (1, "BRICK_1X1"),
)
_BRICK_ID_BY_SPAN = dict(_CANONICAL_SPANNING_BRICKS)


def _internal_joints_from_placements(
    placements: list[BrickPlacement],
    course: int,
    catalog,
) -> frozenset[int]:
    joints: set[int] = set()
    course_placements = sorted(
        (placement for placement in placements if placement.z_plates == course * 3),
        key=lambda placement: placement.x_studs,
    )
    for placement in course_placements:
        brick = catalog.get(placement.brick_id)
        span, depth = brick.footprint(placement.rotation_quarter_turns)
        if depth != 1:
            raise RuntimeError("wall placement expects 1-stud-deep bricks")
        joints.add(placement.x_studs + span)
    return frozenset(joints)


def _choose_segment_composition(
    start_x: int,
    end_x: int,
    previous_joints: frozenset[int],
) -> tuple[int, ...]:
    """Find the best exact composition for [start_x, end_x)."""
    if start_x >= end_x:
        return ()

    @lru_cache(maxsize=None)
    def solve(x_studs: int) -> tuple[int, int, tuple[int, ...]] | None:
        if x_studs == end_x:
            return 0, 0, ()

        best: tuple[int, int, tuple[int, ...]] | None = None
        for span, _ in _CANONICAL_SPANNING_BRICKS:
            end = x_studs + span
            if end > end_x:
                continue

            tail = solve(end)
            if tail is None:
                continue

            tail_overlap, tail_count, tail_spans = tail
            boundary_overlap = 1 if end < end_x and end in previous_joints else 0
            candidate = (
                boundary_overlap + tail_overlap,
                1 + tail_count,
                (span, *tail_spans),
            )
            candidate_key = (
                candidate[0],
                candidate[1],
                tuple(-value for value in candidate[2]),
            )
            if best is None:
                best = candidate
            else:
                best_key = (
                    best[0],
                    best[1],
                    tuple(-value for value in best[2]),
                )
                if candidate_key < best_key:
                    best = candidate

        return best

    result = solve(start_x)
    if result is None:
        raise RuntimeError(f"no exact canonical brick composition for segment {start_x}:{end_x}")
    return result[2]


def _allowed_segments(
    width_studs: int,
    course: int,
    openings: list[WallOpeningGrid],
) -> list[tuple[int, int]]:
    blocked = sorted(
        (opening.x_studs, opening.x_end)
        for opening in openings
        if opening.z_bricks <= course < opening.z_end
    )
    segments: list[tuple[int, int]] = []
    cursor = 0
    for start, end in blocked:
        if cursor < start:
            segments.append((cursor, start))
        cursor = max(cursor, end)
    if cursor < width_studs:
        segments.append((cursor, width_studs))
    return segments


def generate_wall_layout_with_openings(
    width_studs: int,
    height_bricks: int,
    openings: list[WallOpeningGrid] | None = None,
) -> WallBrickLayout:
    """Fill all constructible wall cells while preserving rectangular openings."""
    layout = WallBrickLayout(
        wall_width_studs=width_studs,
        wall_height_bricks=height_bricks,
        openings=list(openings or []),
        placements=[],
    )
    catalog = create_m0_brick_catalog()
    previous_joints: frozenset[int] = frozenset()

    for course in range(height_bricks):
        segments = _allowed_segments(width_studs, course, layout.openings)
        for start_x, end_x in segments:
            composition = _choose_segment_composition(start_x, end_x, previous_joints)
            x = start_x
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

        raw_joints = _internal_joints_from_placements(layout.placements, course, catalog)
        segment_edges = {edge for segment in segments for edge in segment}
        previous_joints = frozenset(
            joint
            for joint in raw_joints
            if joint not in segment_edges and 0 < joint < width_studs
        )

    return layout


def generate_simple_wall_layout(width_studs: int, height_bricks: int) -> WallBrickLayout:
    """Backward-compatible wall generation without openings."""
    return generate_wall_layout_with_openings(width_studs, height_bricks, openings=[])
