import pytest

from brickhouse.building.models import (
    Appearance,
    BuildingModel,
    Facade,
    Metadata,
    Opening,
    OpeningType,
    OpeningVisualDescription,
    Position3D,
    SourceInfo,
    SourceKind,
    Volume,
    VolumeShape,
)
from brickhouse.bricks.architectural_solutions import (
    rank_window_solutions,
    select_facade_window_solutions,
)
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.geometry import generate_building_geometry


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


def _building_with_front_windows(specs):
    source = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)
    return BuildingModel(
        schema_version="0.1",
        id="facade-selection",
        name="Generic facade",
        building_type="house",
        units="m",
        volumes=[Volume(
            id="main", shape=VolumeShape.RECTANGULAR_PRISM,
            position=Position3D(x=0, y=0, z=0), width=10, depth=7, height=6,
            floors=2, source=source,
        )],
        openings=[
            Opening(
                id=opening_id, type=OpeningType.WINDOW, volume_id="main", facade=Facade.FRONT,
                offset_horizontal=x, offset_vertical=z, width=width, height=height, source=source,
                opening_visual=OpeningVisualDescription(leaf_count=leaves, pane_count=panes),
            )
            for opening_id, x, z, width, height, leaves, panes in specs
        ],
        roofs=[], appearance=Appearance(), metadata=Metadata(created_from="synthetic"),
    )


def test_facade_selection_preserves_relative_window_proportions_and_observed_topology():
    building = _building_with_front_windows([
        ("wide", 1.0, 1.0, 1.6, 1.2, 2, 2),
        ("narrow", 5.0, 1.0, 0.8, 1.2, 1, 1),
    ])
    shell = generate_building_brick_shell(generate_building_geometry(building), 24)
    selection = select_facade_window_solutions(
        facade=Facade.FRONT, openings=building.openings, shell=shell
    )
    assert selection is not None
    choices = {choice.opening_id: choice.solution for choice in selection.choices}
    assert choices["wide"].composition == "paired"
    assert choices["narrow"].composition == "single"
    assert choices["wide"].width_studs / choices["narrow"].width_studs == pytest.approx(2.0)
    assert selection.proportion_penalty == pytest.approx(0.0)


def test_facade_selection_does_not_mutate_source_or_raster_geometry():
    building = _building_with_front_windows([
        ("anchor", 1.0, 1.0, 1.0, 1.2, 1, 1),
    ])
    shell = generate_building_brick_shell(generate_building_geometry(building), 30)
    source_before = building.model_dump()
    raster_before = shell.model_dump()
    selection = select_facade_window_solutions(
        facade=Facade.FRONT, openings=building.openings, shell=shell
    )
    assert selection is not None
    assert building.model_dump() == source_before
    assert shell.model_dump() == raster_before
    assert selection.choices[0].source_raster_width_studs == 3
    assert selection.choices[0].solution.width_studs == 2
