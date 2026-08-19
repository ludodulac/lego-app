"""M0 canonical brick catalog."""

from __future__ import annotations

from brickhouse.bricks.models import BrickCatalog, BrickDefinition


_M0_BRICK_SIZES: tuple[tuple[str, int, int], ...] = (
    ("BRICK_1X1", 1, 1),
    ("BRICK_1X2", 1, 2),
    ("BRICK_1X3", 1, 3),
    ("BRICK_1X4", 1, 4),
    ("BRICK_1X6", 1, 6),
    ("BRICK_1X8", 1, 8),
    ("BRICK_2X2", 2, 2),
    ("BRICK_2X3", 2, 3),
    ("BRICK_2X4", 2, 4),
    ("BRICK_2X6", 2, 6),
    ("BRICK_2X8", 2, 8),
    ("BRICK_2X10", 2, 10),
)


def create_m0_brick_catalog() -> BrickCatalog:
    """Create the deterministic canonical standard-brick catalog for M0."""
    return BrickCatalog(
        catalog_id="m0_standard_bricks",
        bricks=[
            BrickDefinition(id=brick_id, width_studs=width, length_studs=length)
            for brick_id, width, length in _M0_BRICK_SIZES
        ],
    )
