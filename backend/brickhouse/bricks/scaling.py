"""Deterministic scaling from metric wall geometry to the brick grid."""

from __future__ import annotations

from math import floor, hypot

from pydantic import BaseModel, Field

from brickhouse.geometry.models import OpeningGeometry, Point3D, WallGeometry

from .placement import WallBrickLayout, WallGridOpening, generate_wall_layout_with_openings

# Physical proportions of the canonical construction grid. A stud pitch is
# 8 mm and one standard brick course (3 plates) is 9.6 mm, so a metric model
# scaled by studs-per-meter uses courses-per-meter = studs-per-meter / 1.2.
COURSES_PER_STUD_RATIO = 1.0 / 1.2


class WallGridSpec(BaseModel):
    wall_id: str
    width_studs: int = Field(gt=0)
    height_bricks: int = Field(gt=0)
    studs_per_meter: float = Field(gt=0)
    courses_per_meter: float = Field(gt=0)
    openings: list[WallGridOpening]


def _round_half_up(value: float) -> int:
    return floor(value + 0.5)


def _distance(a: Point3D, b: Point3D) -> float:
    return hypot(a.x - b.x, a.y - b.y)


def _wall_metric_size(wall: WallGeometry) -> tuple[float, float]:
    if len(wall.corners) != 4:
        raise ValueError("wall geometry must contain exactly four corners")
    width = _distance(wall.corners[0], wall.corners[1])
    height = abs(wall.corners[3].z - wall.corners[0].z)
    if width <= 0 or height <= 0:
        raise ValueError("wall geometry must have positive width and height")
    return width, height


def _opening_local_bounds(wall: WallGeometry, opening: OpeningGeometry) -> tuple[float, float, float, float]:
    wall_start = wall.corners[0]
    wall_end = wall.corners[1]
    vx = wall_end.x - wall_start.x
    vy = wall_end.y - wall_start.y
    wall_width = hypot(vx, vy)
    ux, uy = vx / wall_width, vy / wall_width

    projected = [
        (corner.x - wall_start.x) * ux + (corner.y - wall_start.y) * uy
        for corner in opening.corners
    ]
    vertical = [corner.z - wall_start.z for corner in opening.corners]
    return min(projected), max(projected), min(vertical), max(vertical)


def discretize_wall_geometry(wall: WallGeometry, target_width_studs: int) -> WallGridSpec:
    """Map one metric wall to an integer brick grid using a coherent model scale."""
    if target_width_studs <= 0:
        raise ValueError("target_width_studs must be positive")

    width_m, height_m = _wall_metric_size(wall)
    studs_per_meter = target_width_studs / width_m
    courses_per_meter = studs_per_meter * COURSES_PER_STUD_RATIO
    height_bricks = max(1, _round_half_up(height_m * courses_per_meter))

    grid_openings: list[WallGridOpening] = []
    for opening in wall.openings:
        x0_m, x1_m, z0_m, z1_m = _opening_local_bounds(wall, opening)
        x0 = _round_half_up(x0_m * studs_per_meter)
        x1 = _round_half_up(x1_m * studs_per_meter)
        z0 = _round_half_up(z0_m * courses_per_meter)
        z1 = _round_half_up(z1_m * courses_per_meter)

        x0 = min(max(x0, 0), target_width_studs)
        x1 = min(max(x1, 0), target_width_studs)
        z0 = min(max(z0, 0), height_bricks)
        z1 = min(max(z1, 0), height_bricks)

        if x1 <= x0 or z1 <= z0:
            raise ValueError(
                f"opening {opening.id!r} collapses at target scale {target_width_studs} studs"
            )

        grid_openings.append(
            WallGridOpening(
                id=opening.id,
                x_studs=x0,
                z_bricks=z0,
                width_studs=x1 - x0,
                height_bricks=z1 - z0,
            )
        )

    # WallGridOpening placement validation also rejects overlapping openings.
    return WallGridSpec(
        wall_id=wall.id,
        width_studs=target_width_studs,
        height_bricks=height_bricks,
        studs_per_meter=studs_per_meter,
        courses_per_meter=courses_per_meter,
        openings=grid_openings,
    )


def generate_scaled_wall_layout(wall: WallGeometry, target_width_studs: int) -> WallBrickLayout:
    """Discretize a metric wall and immediately generate its brick layout."""
    spec = discretize_wall_geometry(wall, target_width_studs)
    return generate_wall_layout_with_openings(
        width_studs=spec.width_studs,
        height_bricks=spec.height_bricks,
        openings=spec.openings,
    )
