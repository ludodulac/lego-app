from collections import Counter
from types import SimpleNamespace

from brickhouse.building.models import Facade, OpeningType
from brickhouse.bricks.opening_representation_plan import _generic_two_pane_reservation
from brickhouse.bricks.planned_opening_parts import _emit_compact_two_pane


def _opening():
    return SimpleNamespace(
        id="w",
        facade=Facade.FRONT,
        type=OpeningType.WINDOW,
        opening_visual=SimpleNamespace(pane_count=2, leaf_count=None),
    )


def _raster(height_bricks: int):
    return SimpleNamespace(
        id="w",
        x_studs=0,
        z_bricks=0,
        width_studs=9,
        height_bricks=height_bricks,
    )


def _bom(height_bricks: int):
    placements = []
    assert _emit_compact_two_pane(
        raster=_raster(height_bricks),
        facade=Facade.FRONT,
        front=48,
        depth=40,
        placements=placements,
    )
    return Counter(part.part_id for part in placements)


def test_compact_planner_keeps_exact_footprint_for_9x8_and_9x9():
    for height in (8, 9):
        reservation = _generic_two_pane_reservation(_opening(), _raster(height))
        assert reservation is not None
        assert reservation.status == "reserved"
        assert reservation.motif_id == "compact_two_pane:transparent_panels"
        assert reservation.assembly_id == "compact-two-pane-60581-43337"
        assert reservation.width_studs == 9
        assert reservation.height_bricks == height


def test_compact_9x9_uses_60581_and_center_mullion_only():
    assert _bom(9) == Counter({"PANEL_1X4X3_60581": 6, "BRICK_1X1": 9})


def test_compact_9x8_uses_60581_plus_clear_43337_remainder():
    assert _bom(8) == Counter({
        "PANEL_1X4X3_60581": 4,
        "PANEL_1X4X1_43337": 4,
        "BRICK_1X1": 8,
    })
