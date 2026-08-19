"""Deterministic brick placement for simple rectangular walls."""

from __future__ import annotations

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


def generate_simple_wall_layout(width_studs: int, height_bricks: int) -> WallBrickLayout:
    """Fill a 1-stud-thick rectangular wall using a deterministic greedy strategy.

    BH-005 intentionally ignores openings, staggered joints, structural bonding,
    colors, and metric-to-grid conversion. Each course is filled left-to-right
    using the largest canonical 1xN brick that fits the remaining span.
    """
    layout = WallBrickLayout(
        wall_width_studs=width_studs,
        wall_height_bricks=height_bricks,
        placements=[],
    )
    catalog = create_m0_brick_catalog()

    for course in range(height_bricks):
        x = 0
        remaining = width_studs

        while remaining:
            span, brick_id = next(
                (span, brick_id)
                for span, brick_id in _CANONICAL_SPANNING_BRICKS
                if span <= remaining
            )
            brick = catalog.get(brick_id)
            rotation = 0 if span == 1 else 1
            footprint_x, footprint_y = brick.footprint(rotation)
            if footprint_x != span or footprint_y != 1:
                raise RuntimeError(f"canonical brick {brick_id} does not match wall placement assumptions")

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
            remaining -= span

    return layout
