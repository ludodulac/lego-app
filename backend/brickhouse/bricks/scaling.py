"""Deterministic scaling from metric wall geometry to the brick grid."""

from __future__ import annotations

from math import floor, hypot
from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.geometry.models import OpeningGeometry, Point3D, WallGeometry

from .placement import WallBrickLayout, WallOpeningGrid, generate_wall_layout_with_openings

COURSES_PER_STUD_RATIO = 1.0 / 1.2


class GridSnapError(BaseModel):
    """Signed grid-rounding error for one architectural measurement."""

    quantity: Literal["wall_width", "wall_height", "opening_x", "opening_width", "opening_sill", "opening_height"]
    object_id: str
    source_m: float
    snapped_m: float
    signed_error_m: float
    absolute_error_m: float
    signed_error_units: float
    absolute_error_units: float


class WallDiscretizationQuality(BaseModel):
    wall_id: str
    errors: list[GridSnapError]
    mean_absolute_error_m: float = Field(ge=0)
    worst_absolute_error_m: float = Field(ge=0)


class WallGridSpec(BaseModel):
    wall_id: str
    width_studs: int = Field(gt=0)
    height_bricks: int = Field(gt=0)
    studs_per_meter: float = Field(gt=0)
    courses_per_meter: float = Field(gt=0)
    openings: list[WallOpeningGrid]
    discretization_quality: WallDiscretizationQuality | None = None


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


def _opening_local_bounds(
    wall: WallGeometry,
    opening: OpeningGeometry,
) -> tuple[float, float, float, float]:
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


def _snap_error(quantity: str, object_id: str, source_m: float, snapped_units: int, units_per_meter: float) -> GridSnapError:
    snapped_m = snapped_units / units_per_meter
    signed_error_m = snapped_m - source_m
    signed_error_units = snapped_units - source_m * units_per_meter
    return GridSnapError(
        quantity=quantity,
        object_id=object_id,
        source_m=source_m,
        snapped_m=snapped_m,
        signed_error_m=signed_error_m,
        absolute_error_m=abs(signed_error_m),
        signed_error_units=signed_error_units,
        absolute_error_units=abs(signed_error_units),
    )


def discretize_wall_geometry_at_scale(
    wall: WallGeometry,
    studs_per_meter: float,
) -> WallGridSpec:
    """Map a metric wall and retain an explicit report of grid-rounding loss."""
    if studs_per_meter <= 0:
        raise ValueError("studs_per_meter must be positive")

    width_m, height_m = _wall_metric_size(wall)
    width_studs = max(1, _round_half_up(width_m * studs_per_meter))
    courses_per_meter = studs_per_meter * COURSES_PER_STUD_RATIO
    height_bricks = max(1, _round_half_up(height_m * courses_per_meter))
    errors = [
        _snap_error("wall_width", wall.id, width_m, width_studs, studs_per_meter),
        _snap_error("wall_height", wall.id, height_m, height_bricks, courses_per_meter),
    ]

    grid_openings: list[WallOpeningGrid] = []
    for opening in wall.openings:
        x0_m, x1_m, z0_m, z1_m = _opening_local_bounds(wall, opening)
        x0 = min(max(_round_half_up(x0_m * studs_per_meter), 0), width_studs)
        x1 = min(max(_round_half_up(x1_m * studs_per_meter), 0), width_studs)
        z0 = min(max(_round_half_up(z0_m * courses_per_meter), 0), height_bricks)
        z1 = min(max(_round_half_up(z1_m * courses_per_meter), 0), height_bricks)

        if x1 <= x0 or z1 <= z0:
            raise ValueError(f"opening {opening.id!r} collapses at selected building scale")

        grid_openings.append(
            WallOpeningGrid(
                id=opening.id,
                x_studs=x0,
                z_bricks=z0,
                width_studs=x1 - x0,
                height_bricks=z1 - z0,
            )
        )
        errors.extend([
            _snap_error("opening_x", opening.id, x0_m, x0, studs_per_meter),
            _snap_error("opening_width", opening.id, x1_m - x0_m, x1 - x0, studs_per_meter),
            _snap_error("opening_sill", opening.id, z0_m, z0, courses_per_meter),
            _snap_error("opening_height", opening.id, z1_m - z0_m, z1 - z0, courses_per_meter),
        ])

    quality = WallDiscretizationQuality(
        wall_id=wall.id,
        errors=errors,
        mean_absolute_error_m=sum(error.absolute_error_m for error in errors) / len(errors),
        worst_absolute_error_m=max(error.absolute_error_m for error in errors),
    )
    spec = WallGridSpec(
        wall_id=wall.id,
        width_studs=width_studs,
        height_bricks=height_bricks,
        studs_per_meter=studs_per_meter,
        courses_per_meter=courses_per_meter,
        openings=grid_openings,
        discretization_quality=quality,
    )
    generate_wall_layout_with_openings(
        width_studs=spec.width_studs,
        height_bricks=spec.height_bricks,
        openings=spec.openings,
    )
    return spec


def discretize_wall_geometry(wall: WallGeometry, target_width_studs: int) -> WallGridSpec:
    """Map one wall by deriving scale from its own target width."""
    if target_width_studs <= 0:
        raise ValueError("target_width_studs must be positive")
    width_m, _ = _wall_metric_size(wall)
    return discretize_wall_geometry_at_scale(wall, target_width_studs / width_m)


def generate_scaled_wall_layout(wall: WallGeometry, target_width_studs: int) -> WallBrickLayout:
    """Discretize a metric wall and immediately generate its brick layout."""
    spec = discretize_wall_geometry(wall, target_width_studs)
    return generate_wall_layout_with_openings(
        width_studs=spec.width_studs,
        height_bricks=spec.height_bricks,
        openings=spec.openings,
    )
