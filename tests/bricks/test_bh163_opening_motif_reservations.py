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
from brickhouse.bricks.architectural_solutions import select_facade_window_solutions
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.opening_motifs import opening_motif_by_id
from brickhouse.bricks.window_anchors import apply_architectural_window_anchors
from brickhouse.geometry import generate_building_geometry


def _building(openings: list[Opening]) -> BuildingModel:
    source = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)
    return BuildingModel(
        schema_version="0.1",
        id="bh163-generic",
        name="Generic facade",
        building_type="house",
        units="m",
        volumes=[
            Volume(
                id="main",
                shape=VolumeShape.RECTANGULAR_PRISM,
                position=Position3D(x=0, y=0, z=0),
                width=10,
                depth=7,
                height=6,
                floors=2,
                source=source,
            )
        ],
        openings=openings,
        roofs=[],
        appearance=Appearance(),
        metadata=Metadata(created_from="synthetic"),
    )


def _window(
    opening_id: str,
    *,
    x: float,
    width: float,
    leaves: int,
    panes: int,
) -> Opening:
    source = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)
    return Opening(
        id=opening_id,
        type=OpeningType.WINDOW,
        volume_id="main",
        facade=Facade.FRONT,
        offset_horizontal=x,
        offset_vertical=1.0,
        width=width,
        height=1.2,
        source=source,
        opening_visual=OpeningVisualDescription(
            leaf_count=leaves,
            pane_count=panes,
            glazing="clear",
        ),
    )


def test_facade_solution_reserves_an_exact_curated_motif_before_wall_infill():
    building = _building([
        _window("wide", x=1.0, width=1.6, leaves=2, panes=2),
        _window("narrow", x=5.0, width=0.8, leaves=1, panes=1),
    ])
    shell = generate_building_brick_shell(generate_building_geometry(building), 24)
    source_before = building.model_dump()

    selection = select_facade_window_solutions(
        facade=Facade.FRONT,
        openings=building.openings,
        shell=shell,
    )

    assert selection is not None
    for choice in selection.choices:
        motif = opening_motif_by_id(choice.solution.motif_id)
        assert motif is not None
        assert choice.solution.assembly_id == motif.assembly_id
        assert choice.solution.composition == motif.composition
        assert choice.solution.width_studs == motif.width_studs
        assert choice.solution.height_bricks == motif.height_bricks
        assert choice.solution.leaf_count == motif.leaf_count
        assert choice.solution.pane_count == motif.pane_count

    # Representation planning is downstream-only.
    assert building.model_dump() == source_before


def test_applied_wall_reservations_match_selected_motif_footprints_and_do_not_overlap():
    building = _building([
        _window("left", x=1.0, width=0.8, leaves=1, panes=1),
        _window("right", x=4.0, width=1.6, leaves=2, panes=2),
    ])
    shell = generate_building_brick_shell(generate_building_geometry(building), 24)
    selection = select_facade_window_solutions(
        facade=Facade.FRONT,
        openings=building.openings,
        shell=shell,
    )
    assert selection is not None
    selected = {choice.opening_id: choice.solution for choice in selection.choices}

    application = apply_architectural_window_anchors(building, shell)
    wall = next(item for item in application.shell.walls if item.facade is Facade.FRONT)
    rasters = {raster.id: raster for raster in wall.grid.openings}

    for opening_id, solution in selected.items():
        motif = opening_motif_by_id(solution.motif_id)
        assert motif is not None
        raster = rasters[opening_id]
        assert raster.width_studs == motif.width_studs
        assert raster.height_bricks == motif.height_bricks

    left = rasters["left"]
    right = rasters["right"]
    assert left.x_studs + left.width_studs <= right.x_studs


def test_unknown_glazed_opening_is_not_promoted_into_a_window_motif():
    source = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)
    unknown = Opening(
        id="glazed-unknown",
        type=OpeningType.UNKNOWN,
        volume_id="main",
        facade=Facade.FRONT,
        offset_horizontal=2.0,
        offset_vertical=0.0,
        width=1.6,
        height=2.2,
        source=source,
        opening_visual=OpeningVisualDescription(glazing="clear"),
    )
    building = _building([unknown])
    shell = generate_building_brick_shell(generate_building_geometry(building), 24)
    before = building.model_dump()

    selection = select_facade_window_solutions(
        facade=Facade.FRONT,
        openings=building.openings,
        shell=shell,
    )

    assert selection is None
    assert building.openings[0].type is OpeningType.UNKNOWN
    assert building.openings[0].opening_visual.glazing == "clear"
    assert building.model_dump() == before
