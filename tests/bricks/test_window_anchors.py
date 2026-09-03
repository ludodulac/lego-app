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
from brickhouse.bricks.architectural_solutions import rank_window_solutions
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.placement import WallOpeningGrid
from brickhouse.bricks.window_anchors import (
    _best_start,
    _select_joint_x_starts,
    apply_architectural_window_anchors,
)
from brickhouse.bricks.windows import generate_window_assemblies
from brickhouse.geometry import generate_building_geometry
from brickhouse.pipeline import run_m0_pipeline_model


def _building(*, width=0.8, height=1.2, leaves=None, panes=None, opening_id="window"):
    source = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)
    visual = None
    if leaves is not None or panes is not None:
        visual = OpeningVisualDescription(leaf_count=leaves, pane_count=panes)
    return BuildingModel(
        schema_version="0.1",
        id="window-anchor-house",
        name="Generic window anchor house",
        building_type="house",
        units="m",
        volumes=[Volume(
            id="main",
            shape=VolumeShape.RECTANGULAR_PRISM,
            position=Position3D(x=0, y=0, z=0),
            width=10,
            depth=7,
            height=6,
            floors=2,
            source=source,
        )],
        openings=[Opening(
            id=opening_id,
            type=OpeningType.WINDOW,
            volume_id="main",
            facade=Facade.FRONT,
            offset_horizontal=1.0,
            offset_vertical=1.0,
            width=width,
            height=height,
            source=source,
            opening_visual=visual,
        )],
        roofs=[],
        appearance=Appearance(),
        metadata=Metadata(created_from="synthetic"),
    )


def _opening(*, opening_id, x, z=1.0, width=3.0, height=2.0):
    source = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)
    return Opening(
        id=opening_id,
        type=OpeningType.WINDOW,
        volume_id="main",
        facade=Facade.FRONT,
        offset_horizontal=x,
        offset_vertical=z,
        width=width,
        height=height,
        source=source,
    )


def test_missing_topology_never_invents_paired_or_four_pane_joinery():
    selection = rank_window_solutions(
        architectural_width_m=1.6,
        architectural_height_m=1.2,
        raster_width_studs=4,
        raster_height_bricks=3,
    )
    assert selection.candidates
    assert {candidate.composition for candidate in selection.candidates} == {"single"}


def test_joint_anchor_search_preserves_spacing_when_independent_rounding_would_overlap():
    left = _opening(opening_id="left", x=3.0)
    right = _opening(opening_id="right", x=5.01)
    left_raster = WallOpeningGrid(id="left", x_studs=3, z_bricks=1, width_studs=3, height_bricks=2)
    right_raster = WallOpeningGrid(id="right", x_studs=6, z_bricks=1, width_studs=3, height_bricks=2)

    assert _best_start(
        metric_offset=left.offset_horizontal,
        metric_size=left.width,
        units_per_meter=1.0,
        span_units=3,
        wall_span_units=12,
        source_start=left_raster.x_studs,
    ) == 3
    assert _best_start(
        metric_offset=right.offset_horizontal,
        metric_size=right.width,
        units_per_meter=1.0,
        span_units=3,
        wall_span_units=12,
        source_start=right_raster.x_studs,
    ) == 5

    starts = _select_joint_x_starts(
        records=[
            (left, left_raster, 3, 2, 1),
            (right, right_raster, 3, 2, 1),
        ],
        studs_per_meter=1.0,
        wall_width_studs=12,
    )

    assert starts == {"left": 3, "right": 6}
    assert starts["left"] + 3 <= starts["right"]


def test_joint_anchor_search_allows_stacked_openings_to_share_horizontal_anchor():
    lower = _opening(opening_id="lower", x=3.0, z=1.0)
    upper = _opening(opening_id="upper", x=3.0, z=4.0)
    lower_raster = WallOpeningGrid(id="lower", x_studs=3, z_bricks=1, width_studs=3, height_bricks=2)
    upper_raster = WallOpeningGrid(id="upper", x_studs=3, z_bricks=4, width_studs=3, height_bricks=2)

    starts = _select_joint_x_starts(
        records=[
            (lower, lower_raster, 3, 2, 1),
            (upper, upper_raster, 3, 2, 4),
        ],
        studs_per_meter=1.0,
        wall_width_studs=12,
    )

    assert starts == {"lower": 3, "upper": 3}


def test_joint_anchor_search_refuses_overlapping_same_level_openings_without_valid_alternative():
    first = _opening(opening_id="first", x=3.0)
    second = _opening(opening_id="second", x=3.0)
    first_raster = WallOpeningGrid(id="first", x_studs=3, z_bricks=1, width_studs=3, height_bricks=2)
    second_raster = WallOpeningGrid(id="second", x_studs=3, z_bricks=1, width_studs=3, height_bricks=2)

    starts = _select_joint_x_starts(
        records=[
            (first, first_raster, 3, 2, 1),
            (second, second_raster, 3, 2, 1),
        ],
        studs_per_meter=1.0,
        wall_width_studs=12,
    )

    assert starts is None


def test_anchor_application_changes_only_derived_lego_shell_and_refills_wall():
    building = _building(width=1.0, height=1.2, leaves=1, panes=1)
    source_before = building.model_dump()
    shell = generate_building_brick_shell(generate_building_geometry(building), 30)
    front_before = next(wall for wall in shell.walls if wall.facade is Facade.FRONT)
    raster_before = front_before.grid.openings[0]
    assert raster_before.width_studs == 3
    assert raster_before.height_bricks == 3

    result = apply_architectural_window_anchors(building, shell)
    front_after = next(wall for wall in result.shell.walls if wall.facade is Facade.FRONT)
    raster_after = front_after.grid.openings[0]

    assert building.model_dump() == source_before
    assert raster_after.width_studs == 2
    assert raster_after.height_bricks == 2
    assert front_after.layout.openings == front_after.grid.openings
    assert result.anchors[0].geometry_changed


def test_evidence_backed_paired_solution_is_rendered_as_two_real_window_modules():
    building = _building(width=1.6, height=1.2, leaves=2, panes=2)
    shell = generate_building_brick_shell(generate_building_geometry(building), 24)
    result = apply_architectural_window_anchors(building, shell)
    selected = {anchor.opening_id: (anchor.composition, anchor.assembly_id) for anchor in result.anchors}

    parts, fitted = generate_window_assemblies(
        building,
        result.shell,
        selected_solutions=selected,
    )
    frames = [part for part in parts if part.category == "window_frame"]
    panes = [part for part in parts if part.category == "window_pane"]

    assert fitted == {"window"}
    assert len(frames) == 2
    assert len(panes) == 2
    assert {frame.part_id for frame in frames} == {"WINDOW_1X2X2_60592"}


def test_pipeline_surfaces_local_anchor_adjustment_and_uses_selected_frame():
    building = _building(width=1.0, height=1.2, leaves=1, panes=1)
    bundle = run_m0_pipeline_model(building, front_width_studs=30)

    assert any(
        issue.code == "lego_window_local_anchor_adjustment" and issue.object_id == "window"
        for issue in bundle.fidelity_issues
    )
    frames = [part for part in bundle.brick_model.parts if part.category == "window_frame"]
    assert len(frames) == 1
    assert frames[0].part_id == "WINDOW_1X2X2_60592"
