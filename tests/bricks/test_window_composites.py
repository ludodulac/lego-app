from brickhouse.building.models import WindowStyle
from brickhouse.bricks.windows import choose_window_layout


def _covered_cells(layout):
    cells = set()
    for assembly, x0, z0 in layout:
        for x in range(x0, x0 + assembly.width_studs):
            for z in range(z0, z0 + assembly.height_bricks):
                assert (x, z) not in cells
                cells.add((x, z))
    return cells


def test_simple_six_by_six_window_uses_validated_assemblies_without_masonry_gap() -> None:
    layout = choose_window_layout(WindowStyle.SIMPLE, 6, 6)
    assert layout
    assert _covered_cells(layout) == {(x, z) for x in range(6) for z in range(6)}


def test_unsupported_odd_width_does_not_fake_a_stretched_window() -> None:
    assert choose_window_layout(WindowStyle.SIMPLE, 7, 6) == ()


def test_tall_window_prefers_three_brick_high_real_modules() -> None:
    layout = choose_window_layout(WindowStyle.TRADITIONAL_TALL, 4, 6)
    assert layout
    assert all(assembly.height_bricks == 3 for assembly, _, _ in layout)
    assert _covered_cells(layout) == {(x, z) for x in range(4) for z in range(6)}
