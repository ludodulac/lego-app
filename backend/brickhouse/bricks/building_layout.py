"""Building-level brick wall generation at one shared scale."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building.models import Facade
from brickhouse.geometry.models import BuildingGeometry, WallGeometry

from .placement import WallBrickLayout, generate_wall_layout_with_openings
from .scaling import WallGridSpec, _wall_metric_size, discretize_wall_geometry_at_scale


class BuildingWallLayout(BaseModel):
    wall_id: str
    facade: Facade
    grid: WallGridSpec
    layout: WallBrickLayout


class BuildingBrickShell(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    building_id: str
    volume_id: str
    reference_facade: Literal["front"] = "front"
    reference_width_studs: int = Field(gt=0)
    studs_per_meter: float = Field(gt=0)
    walls: list[BuildingWallLayout] = Field(min_length=4, max_length=4)


def _validate_single_rectangular_shell(geometry: BuildingGeometry) -> dict[Facade, WallGeometry]:
    if len(geometry.walls) != 4:
        raise ValueError("M0 building shell requires exactly four walls")

    volume_ids = {wall.volume_id for wall in geometry.walls}
    if len(volume_ids) != 1:
        raise ValueError("M0 building shell requires all four walls to belong to one volume")

    by_facade: dict[Facade, WallGeometry] = {}
    for wall in geometry.walls:
        if wall.facade in by_facade:
            raise ValueError(f"duplicate wall for facade {wall.facade.value!r}")
        by_facade[wall.facade] = wall

    required = {Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT}
    if set(by_facade) != required:
        raise ValueError("M0 building shell requires front, rear, left and right walls")

    front_width, front_height = _wall_metric_size(by_facade[Facade.FRONT])
    rear_width, rear_height = _wall_metric_size(by_facade[Facade.REAR])
    left_width, left_height = _wall_metric_size(by_facade[Facade.LEFT])
    right_width, right_height = _wall_metric_size(by_facade[Facade.RIGHT])

    tolerance = 1e-8
    if abs(front_width - rear_width) > tolerance:
        raise ValueError("front and rear walls must have equal metric width")
    if abs(left_width - right_width) > tolerance:
        raise ValueError("left and right walls must have equal metric width")
    heights = [front_height, rear_height, left_height, right_height]
    if max(heights) - min(heights) > tolerance:
        raise ValueError("all four walls must have equal metric height")

    return by_facade


def generate_building_brick_shell(
    geometry: BuildingGeometry,
    front_width_studs: int,
) -> BuildingBrickShell:
    """Generate four wall layouts using one scale derived from the front wall."""
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")

    by_facade = _validate_single_rectangular_shell(geometry)
    front_width_m, _ = _wall_metric_size(by_facade[Facade.FRONT])
    studs_per_meter = front_width_studs / front_width_m

    wall_records: list[BuildingWallLayout] = []
    for facade in (Facade.FRONT, Facade.REAR, Facade.LEFT, Facade.RIGHT):
        wall = by_facade[facade]
        grid = discretize_wall_geometry_at_scale(wall, studs_per_meter)
        layout = generate_wall_layout_with_openings(
            width_studs=grid.width_studs,
            height_bricks=grid.height_bricks,
            openings=grid.openings,
        )
        wall_records.append(
            BuildingWallLayout(
                wall_id=wall.id,
                facade=facade,
                grid=grid,
                layout=layout,
            )
        )

    heights = {record.grid.height_bricks for record in wall_records}
    if len(heights) != 1:
        raise RuntimeError("shared scale produced inconsistent wall heights")

    return BuildingBrickShell(
        building_id=geometry.building_id,
        volume_id=geometry.walls[0].volume_id,
        reference_width_studs=front_width_studs,
        studs_per_meter=studs_per_meter,
        walls=wall_records,
    )
