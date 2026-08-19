"""Canonical brick definitions used by the BrickHouse engine."""

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
    generate_scaled_wall_layout,
)

__all__ = [
    "BrickCatalog",
    "BrickDefinition",
    "BrickPlacement",
    "WallBrickLayout",
    "WallGridSpec",
    "WallOpeningGrid",
    "create_m0_brick_catalog",
    "discretize_wall_geometry",
    "generate_scaled_wall_layout",
    "generate_simple_wall_layout",
    "generate_wall_layout_with_openings",
]
