from brickhouse.bricks.windows import VALIDATED_WINDOW_ASSEMBLIES, choose_window_assembly, _to_global
from brickhouse.building.models import Facade


def test_validated_window_families_are_explicit_and_unique():
    dimensions = {(a.width_studs, a.height_bricks) for a in VALIDATED_WINDOW_ASSEMBLIES}
    assert dimensions == {(2, 2), (2, 3), (4, 3)}
    assert len({a.id for a in VALIDATED_WINDOW_ASSEMBLIES}) == 3


def test_choose_window_assembly_requires_exact_fit():
    assert choose_window_assembly(2, 2).frame_part_id == "WINDOW_1X2X2_60592"
    assert choose_window_assembly(2, 3).pane_part_id == "GLASS_FOR_WINDOW_1X2X3_60602"
    assert choose_window_assembly(4, 3).frame_part_id == "WINDOW_1X4X3_60594"
    assert choose_window_assembly(3, 3) is None
    assert choose_window_assembly(4, 2) is None


def test_window_global_mapping_runs_long_axis_along_each_facade():
    assert _to_global(Facade.FRONT, 3, 4, 2, 20, 14) == (3, 0, 6, 1)
    assert _to_global(Facade.REAR, 3, 4, 2, 20, 14) == (13, 13, 6, 1)
    assert _to_global(Facade.RIGHT, 3, 4, 2, 20, 14) == (19, 3, 6, 0)
    assert _to_global(Facade.LEFT, 3, 4, 2, 20, 14) == (0, 7, 6, 0)
