from brickhouse.building.models import (
    Facade,
    Opening,
    OpeningType,
    SourceInfo,
    SourceKind,
)
from brickhouse.bricks.placement import WallOpeningGrid
from brickhouse.bricks.window_anchors import _best_start, _select_joint_z_starts


def _opening(*, opening_id: str, z: float) -> Opening:
    return Opening(
        id=opening_id,
        type=OpeningType.WINDOW,
        volume_id="main",
        facade=Facade.FRONT,
        offset_horizontal=1.0,
        offset_vertical=z,
        width=1.0,
        height=2.0,
        source=SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9),
    )


def test_joint_vertical_anchor_search_preserves_relative_row_spacing():
    low = _opening(opening_id="low", z=1.0)
    middle = _opening(opening_id="middle", z=1.2)
    high = _opening(opening_id="high", z=1.51)
    rasters = [
        WallOpeningGrid(id="low", x_studs=1, z_bricks=1, width_studs=2, height_bricks=2),
        WallOpeningGrid(id="middle", x_studs=4, z_bricks=1, width_studs=2, height_bricks=2),
        WallOpeningGrid(id="high", x_studs=7, z_bricks=2, width_studs=2, height_bricks=2),
    ]

    independent = [
        _best_start(
            metric_offset=opening.offset_vertical,
            metric_size=opening.height,
            units_per_meter=1.0,
            span_units=2,
            wall_span_units=12,
            source_start=raster.z_bricks,
        )
        for opening, raster in zip((low, middle, high), rasters)
    ]
    assert independent == [1, 1, 2]

    joint = _select_joint_z_starts(
        records=[
            (low, rasters[0], 2),
            (middle, rasters[1], 2),
            (high, rasters[2], 2),
        ],
        courses_per_meter=1.0,
        wall_height_bricks=12,
    )

    assert joint == {"low": 1, "middle": 1, "high": 1}


def test_joint_vertical_anchor_search_never_inverts_architectural_order():
    lower = _opening(opening_id="lower", z=1.49)
    upper = _opening(opening_id="upper", z=1.51)
    lower_raster = WallOpeningGrid(
        id="lower", x_studs=1, z_bricks=1, width_studs=2, height_bricks=2
    )
    upper_raster = WallOpeningGrid(
        id="upper", x_studs=5, z_bricks=2, width_studs=2, height_bricks=2
    )

    joint = _select_joint_z_starts(
        records=[
            (lower, lower_raster, 2),
            (upper, upper_raster, 2),
        ],
        courses_per_meter=1.0,
        wall_height_bricks=12,
    )

    assert joint is not None
    assert joint["lower"] <= joint["upper"]
