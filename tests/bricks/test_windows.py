from brickhouse.bricks.windows import VALIDATED_WINDOW_ASSEMBLIES, choose_window_assembly, choose_window_layout, _to_global
from brickhouse.building.models import Facade, WindowStyle


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


def test_style_layout_is_faithful_instead_of_merely_dimensionally_possible():
    simple = choose_window_layout(WindowStyle.SIMPLE, 4, 3)
    assert len(simple) == 1 and simple[0][0].frame_part_id == "WINDOW_1X4X3_60594"
    paired = choose_window_layout(WindowStyle.PAIRED, 4, 3)
    assert [offset for _, offset, _ in paired] == [0, 2]
    assert all(a.frame_part_id == "WINDOW_1X2X3_60593" for a, _, _ in paired)
    assert choose_window_layout(WindowStyle.BAY, 4, 3) == ()
    assert choose_window_layout(WindowStyle.TRADITIONAL_TALL, 2, 2) == ()
    assert choose_window_layout(WindowStyle.TRADITIONAL_TALL, 2, 3)


def test_simple_window_never_gets_fake_mullions_or_transoms_to_fill_large_void():
    # These rectangles can be tiled dimensionally with validated frames, but a
    # SIMPLE style does not prove any internal joinery. Keep the opening clean.
    assert choose_window_layout(WindowStyle.SIMPLE, 4, 6) == ()
    assert choose_window_layout(WindowStyle.SIMPLE, 8, 3) == ()


def test_paired_style_allows_only_the_observed_single_vertical_division():
    assert len(choose_window_layout(WindowStyle.PAIRED, 4, 2)) == 2
    assert len(choose_window_layout(WindowStyle.PAIRED, 4, 3)) == 2
    assert choose_window_layout(WindowStyle.PAIRED, 4, 6) == ()
    assert choose_window_layout(WindowStyle.PAIRED, 8, 3) == ()


def test_four_pane_style_is_the_only_current_style_that_authorizes_two_by_two_frames():
    four = choose_window_layout(WindowStyle.FOUR_PANE, 4, 6)
    assert [(x, z) for _, x, z in four] == [(0, 0), (2, 0), (0, 3), (2, 3)]
    assert all(a.frame_part_id == "WINDOW_1X2X3_60593" for a, _, _ in four)
    assert choose_window_layout(WindowStyle.FOUR_PANE, 4, 3) == ()


def test_window_global_mapping_runs_long_axis_along_each_facade():
    assert _to_global(Facade.FRONT, 3, 4, 2, 20, 14) == (3, 0, 6, 1)
    assert _to_global(Facade.REAR, 3, 4, 2, 20, 14) == (13, 13, 6, 1)
    assert _to_global(Facade.RIGHT, 3, 4, 2, 20, 14) == (19, 3, 6, 0)
    assert _to_global(Facade.LEFT, 3, 4, 2, 20, 14) == (0, 7, 6, 0)
