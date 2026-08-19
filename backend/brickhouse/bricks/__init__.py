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

__all__ = [
    "BrickCatalog",
    "BrickDefinition",
    "BrickPlacement",
    "WallBrickLayout",
    "WallOpeningGrid",
    "create_m0_brick_catalog",
    "generate_simple_wall_layout",
    "generate_wall_layout_with_openings",
]
