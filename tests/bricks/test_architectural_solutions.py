import pytest

from brickhouse.bricks.architectural_solutions import rank_window_solutions


def test_simple_window_prefers_matching_validated_family_without_grid_adjustment():
    selection = rank_window_solutions(
        architectural_width_m=0.8,
        architectural_height_m=1.2,
        raster_width_studs=2,
        raster_height_bricks=3,
        observed_leaf_count=1,
        observed_pane_count=1,
    )

    assert selection.recommended is not None
    assert selection.recommended.composition == "single"
    assert selection.recommended.assembly_id == "window-1x2x3-60593-60602"
    assert selection.recommended.grid_adjustment_studs == 0
    assert selection.recommended.grid_adjustment_bricks == 0


def test_observed_paired_composition_beats_single_frame_with_same_outer_raster():
    selection = rank_window_solutions(
        architectural_width_m=1.6,
        architectural_height_m=1.2,
        raster_width_studs=4,
        raster_height_bricks=3,
        observed_leaf_count=2,
        observed_pane_count=2,
    )

    assert selection.recommended is not None
    assert selection.recommended.composition == "paired"
    assert selection.recommended.assembly_id == "window-1x2x3-60593-60602"
    assert selection.recommended.leaf_count == 2
    assert selection.recommended.pane_count == 2


def test_four_pane_topology_is_ranked_as_architectural_identity_not_generic_glazing():
    selection = rank_window_solutions(
        architectural_width_m=1.2,
        architectural_height_m=1.8,
        raster_width_studs=4,
        raster_height_bricks=6,
        observed_leaf_count=2,
        observed_pane_count=4,
    )

    assert selection.recommended is not None
    assert selection.recommended.composition == "four_pane"
    assert selection.recommended.assembly_id == "window-1x2x3-60593-60602"
    assert selection.recommended.module_count == 4


def test_local_anchor_adjustment_is_reported_but_source_dimensions_are_unchanged():
    selection = rank_window_solutions(
        architectural_width_m=0.8,
        architectural_height_m=1.2,
        raster_width_studs=3,
        raster_height_bricks=3,
        observed_leaf_count=1,
        observed_pane_count=1,
        max_local_adjustment_studs=1,
    )

    assert selection.architectural_width_m == pytest.approx(0.8)
    assert selection.architectural_height_m == pytest.approx(1.2)
    assert selection.raster_width_studs == 3
    assert selection.recommended is not None
    assert selection.recommended.width_studs == 2
    assert selection.recommended.grid_adjustment_studs == 1


def test_local_anchor_candidates_respect_explicit_adjustment_bounds():
    selection = rank_window_solutions(
        architectural_width_m=0.8,
        architectural_height_m=1.2,
        raster_width_studs=3,
        raster_height_bricks=3,
        observed_leaf_count=1,
        observed_pane_count=1,
        max_local_adjustment_studs=0,
        max_local_adjustment_bricks=0,
    )

    assert selection.recommended is None
    assert selection.candidates == []


def test_invalid_observed_topology_is_rejected_instead_of_invented():
    with pytest.raises(ValueError, match="observed_leaf_count"):
        rank_window_solutions(
            architectural_width_m=1.0,
            architectural_height_m=1.0,
            raster_width_studs=2,
            raster_height_bricks=2,
            observed_leaf_count=0,
        )
