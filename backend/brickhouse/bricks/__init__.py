"""Canonical brick definitions used by the BrickHouse engine."""

from brickhouse.bricks.building_layout import (
    BuildingBrickShell,
    BuildingWallLayout,
    generate_building_brick_shell,
)
from brickhouse.bricks.catalog import create_m0_brick_catalog
from brickhouse.bricks.models import BrickCatalog, BrickDefinition
from brickhouse.bricks.placement import (
    BrickPlacement,
    WallBrickLayout,
    WallOpeningGrid,
    generate_simple_wall_layout,
    generate_wall_layout_with_openings,
)
from brickhouse.bricks.scaling import (
    WallGridSpec,
    discretize_wall_geometry,
    discretize_wall_geometry_at_scale,
    generate_scaled_wall_layout,
)
from brickhouse.bricks.spatial import (
    GlobalBrickPlacement,
    SpatialBrickShell,
    generate_spatial_brick_shell,
)

__all__ = [
    "BrickCatalog",
    "BrickDefinition",
    "BrickPlacement",
    "BuildingBrickShell",
    "BuildingWallLayout",
    "GlobalBrickPlacement",
    "SpatialBrickShell",
    "WallBrickLayout",
    "WallGridSpec",
    "WallOpeningGrid",
    "create_m0_brick_catalog",
    "discretize_wall_geometry",
    "discretize_wall_geometry_at_scale",
    "generate_building_brick_shell",
    "generate_scaled_wall_layout",
    "generate_simple_wall_layout",
    "generate_spatial_brick_shell",
    "generate_wall_layout_with_openings",
]
