from copy import deepcopy

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
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.opening_motifs import opening_motif_by_id
from brickhouse.bricks.opening_plan_anchors import apply_opening_representation_plan
from brickhouse.bricks.opening_representation_plan import build_opening_representation_plan
from brickhouse.bricks.planned_opening_parts import generate_planned_opening_parts
from brickhouse.bricks.windows import VALIDATED_WINDOW_ASSEMBLIES
from brickhouse.geometry import generate_building_geometry


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)


def _opening(
    opening_id: str,
    opening_type: OpeningType,
    *,
    x: float,
    width: float,
    height: float,
    glazing: str | None = None,
    leaves: int | None = None,
    panes: int | None = None,
) -> Opening:
    return Opening(
        id=opening_id,
        type=opening_type,
        volume_id="main",
        facade=Facade.FRONT,
        offset_horizontal=x,
        offset_vertical=0.0 if opening_type is not OpeningType.WINDOW else 1.0,
        width=width,
        height=height,
        source=SOURCE,
        opening_visual=OpeningVisualDescription(
            glazing=glazing,
            leaf_count=leaves,
            pane_count=panes,
        ),
    )


def _building(openings: list[Opening]) -> BuildingModel:
    return BuildingModel(
        schema_version="0.1",
        id="opening-plan-generic",
        name="Opening representation plan fixture",
        building_type="building",
        units="m",
        volumes=[Volume(
            id="main",
            shape=VolumeShape.RECTANGULAR_PRISM,
            position=Position3D(x=0, y=0, z=0),
            width=10,
            depth=7,
            height=6,
            floors=2,
            source=SOURCE,
        )],
        openings=openings,
        roofs=[],
        appearance=Appearance(),
        metadata=Metadata(created_from="synthetic"),
    )


def _shell(building):
    return generate_building_brick_shell(generate_building_geometry(building), 24)


def test_plan_preserves_window_door_and_unknown_semantics_while_reserving_curated_motifs():
    building = _building([
        _opening("window", OpeningType.WINDOW, x=0.8, width=0.8, height=1.5, glazing="clear", leaves=1, panes=1),
        _opening("door", OpeningType.DOOR, x=3.0, width=1.6, height=2.0, glazing="clear", leaves=2, panes=2),
        _opening("unknown", OpeningType.UNKNOWN, x=6.5, width=1.6, height=1.5, glazing="clear"),
    ])
    before = deepcopy(building.model_dump())

    plan = build_opening_representation_plan(building, _shell(building))

    window = plan.reservation("window")
    door = plan.reservation("door")
    unknown = plan.reservation("unknown")
    assert window.status == "reserved" and window.representation_role == "window"
    assert door.status == "reserved" and door.representation_role == "glazed_door"
    assert door.architectural_type is OpeningType.DOOR
    assert door.support_requirement == "threshold_or_surrounding_wall_bearing"
    assert unknown.status == "reserved" and unknown.representation_role == "neutral_glazed"
    assert unknown.architectural_type is OpeningType.UNKNOWN
    assert building.model_dump() == before


def test_unknown_without_structured_glazing_is_explicitly_unsupported_not_promoted():
    opening = _opening("unknown", OpeningType.UNKNOWN, x=2.0, width=1.6, height=1.5)
    building = _building([opening])

    reservation = build_opening_representation_plan(building, _shell(building)).reservation("unknown")

    assert reservation.status == "unsupported"
    assert reservation.motif_id is None
    assert "structured glazing evidence" in reservation.reason
    assert building.openings[0].type is OpeningType.UNKNOWN


def test_known_but_unsupported_composition_returns_blocker_instead_of_inventing_joinery():
    opening = _opening(
        "unsupported-window",
        OpeningType.WINDOW,
        x=2.0,
        width=1.6,
        height=1.5,
        glazing="clear",
        leaves=3,
        panes=7,
    )
    building = _building([opening])

    plan = build_opening_representation_plan(building, _shell(building))
    reservation = plan.reservation("unsupported-window")

    assert reservation.status == "unsupported"
    assert reservation in plan.blockers
    assert reservation.motif_id is None


def test_application_reserves_exact_motif_footprint_before_spatial_wall_infill_without_source_mutation():
    building = _building([
        _opening("door", OpeningType.DOOR, x=2.0, width=1.6, height=2.0, glazing="clear", leaves=2, panes=2),
        _opening("unknown", OpeningType.UNKNOWN, x=6.0, width=1.6, height=1.5, glazing="clear"),
    ])
    shell = _shell(building)
    building_before = deepcopy(building.model_dump())
    shell_before = deepcopy(shell.model_dump())
    plan = build_opening_representation_plan(building, shell)

    application = apply_opening_representation_plan(building, shell, plan)
    wall = next(item for item in application.shell.walls if item.facade is Facade.FRONT)
    rasters = {item.id: item for item in wall.grid.openings}

    assert not application.rejected_facades
    for opening_id in ("door", "unknown"):
        reservation = plan.reservation(opening_id)
        motif = opening_motif_by_id(reservation.motif_id)
        assert rasters[opening_id].width_studs == motif.width_studs
        assert rasters[opening_id].height_bricks == motif.height_bricks
    assert building.model_dump() == building_before
    assert shell.model_dump() == shell_before


def test_planned_parts_use_only_validated_frame_pane_assemblies_and_never_fake_glazing_with_standard_bricks():
    building = _building([
        _opening("door", OpeningType.DOOR, x=2.0, width=1.6, height=2.0, glazing="clear", leaves=2, panes=2),
        _opening("unknown", OpeningType.UNKNOWN, x=6.0, width=1.6, height=1.5, glazing="clear"),
    ])
    shell = _shell(building)
    plan = build_opening_representation_plan(building, shell)
    application = apply_opening_representation_plan(building, shell, plan)

    parts, represented, statuses = generate_planned_opening_parts(
        building,
        application.shell,
        plan,
    )

    validated_ids = {
        part_id
        for assembly in VALIDATED_WINDOW_ASSEMBLIES
        for part_id in (assembly.frame_part_id, assembly.pane_part_id)
    }
    assert represented == {"door", "unknown"}
    assert all(status.represented for status in statuses)
    assert parts
    assert {part.part_id for part in parts}.issubset(validated_ids)
    assert all(part.part_id != "BRICK_1X1" for part in parts)
    assert {part.opening_id for part in parts} == {"door", "unknown"}
