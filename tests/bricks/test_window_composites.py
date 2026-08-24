from brickhouse.building.models import WindowStyle
from brickhouse.bricks.windows import choose_window_layout


def test_large_simple_window_does_not_invent_frame_subdivisions() -> None:
    # A simple 6x6 architectural opening has no exact validated real-frame
    # assembly. It must stay joinery-free at this selection layer rather than
    # being tiled into several smaller frames merely to fill the raster.
    assert choose_window_layout(WindowStyle.SIMPLE, 6, 6) == ()


def test_unsupported_odd_width_does_not_fake_a_stretched_window() -> None:
    assert choose_window_layout(WindowStyle.SIMPLE, 7, 6) == ()


def test_large_traditional_tall_window_does_not_invent_grid_of_modules() -> None:
    # traditional_tall identifies the opening family; it does not prove a 2x2
    # grid of separate physical frames. Unsupported large geometry falls back to
    # joinery-free glazing later in the pipeline.
    assert choose_window_layout(WindowStyle.TRADITIONAL_TALL, 4, 6) == ()
