from copy import deepcopy

import brickhouse.bricks.opening_plan_anchors as anchors_module
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
from brickhouse.bricks.opening_plan_anchors import (
    AppliedOpeningAnchor,
    OpeningRepresentationAdjustment,
    apply_opening_representation_plan,
)
from brickhouse.bricks.opening_representation_plan import build_opening_representation_plan
from brickhouse.geometry import generate_building_geometry


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)


def _opening(opening_id: str, x: float) -> Opening:
    return Opening(
        id=opening_id,
        type=OpeningType.UNKNOWN,
        volume_id="main",
        facade=Facade.FRONT,
        offset_horizontal=x,
        offset_vertical=0.0,
        width=1.6,
        height=1.5,
        source=SOURCE,
        opening_visual=OpeningVisualDescription(glazing="clear"),
    )


def _building(openings: list[Opening]) -> BuildingModel:
    return BuildingModel(
        schema_version="0.1",
        id="bh177-generic",
        name="Bounded opening adjustment fixture",
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


def _fixture(openings: list[Opening]):
    building = _building(openings)
    shell = generate_building_brick_shell(generate_building_geometry(building), 24)
    plan = build_opening_representation_plan(building, shell)
    assert all(plan.reservation(item.id).status == "reserved" for item in openings)
    return building, shell, plan


def _anchor(**updates) -> AppliedOpeningAnchor:
    values = dict(
        opening_id="opening",
        facade=Facade.FRONT,
        representation_role="neutral_glazed",
        motif_id="motif",
        assembly_id="assembly",
        source_x_studs=5,
        source_z_bricks=2,
        source_width_studs=4,
        source_height_bricks=3,
        anchored_x_studs=5,
        anchored_z_bricks=2,
        anchored_width_studs=4,
        anchored_height_bricks=3,
    )
    values.update(updates)
    return AppliedOpeningAnchor(**values)


def test_adjustment_diagnostic_serializes_zero_and_one_unit_deltas_deterministically():
    unchanged = OpeningRepresentationAdjustment.from_anchor(_anchor())
    bounded = OpeningRepresentationAdjustment.from_anchor(_anchor(
        anchored_x_studs=6,
        anchored_z_bricks=1,
        anchored_width_studs=5,
        anchored_height_bricks=2,
    ))

    assert unchanged.status == "unchanged"
    assert unchanged.model_dump() == OpeningRepresentationAdjustment.from_anchor(_anchor()).model_dump()
    assert bounded.status == "bounded"
    assert bounded.within_local_bounds
    assert bounded.model_dump() == {
        "opening_id": "opening",
        "facade": Facade.FRONT,
        "status": "bounded",
        "delta_x_studs": 1,
        "delta_z_bricks": -1,
        "delta_width_studs": 1,
        "delta_height_bricks": -1,
    }


def test_application_rejects_translation_outside_one_unit_envelope_atomically(monkeypatch):
    building, shell, plan = _fixture([_opening("opening", 2.0)])
    before_building = deepcopy(building.model_dump())
    before_shell = shell.model_dump()

    monkeypatch.setattr(
        anchors_module,
        "_select_joint_z_starts",
        lambda **kwargs: {opening.id: raster.z_bricks for opening, raster, _ in kwargs["records"]},
    )
    monkeypatch.setattr(
        anchors_module,
        "_select_joint_x_starts",
        lambda **kwargs: {opening.id: raster.x_studs + 2 for opening, raster, *_ in kwargs["records"]},
    )

    application = apply_opening_representation_plan(building, shell, plan)

    assert building.model_dump() == before_building
    assert shell.model_dump() == before_shell
    assert application.shell.model_dump() == before_shell
    assert application.anchors == []
    assert application.adjustments == []
    assert application.rejected_facades == [Facade.FRONT]
    assert application.rejections[0].code == "adjustment_exceeds_local_bound"
    assert application.rejections[0].severity == "blocker"


def test_application_rejects_left_right_inversion_before_committing_facade(monkeypatch):
    building, shell, plan = _fixture([
        _opening("left", 2.0),
        _opening("right", 6.0),
    ])
    front = next(wall for wall in shell.walls if wall.facade is Facade.FRONT)
    source_by_id = {raster.id: raster for raster in front.grid.openings}

    monkeypatch.setattr(
        anchors_module,
        "_select_joint_z_starts",
        lambda **kwargs: {opening.id: raster.z_bricks for opening, raster, _ in kwargs["records"]},
    )

    def inverted_x(**kwargs):
        records = kwargs["records"]
        starts = {opening.id: raster.x_studs for opening, raster, *_ in records}
        starts["left"] = source_by_id["right"].x_studs
        starts["right"] = source_by_id["left"].x_studs
        return starts

    monkeypatch.setattr(anchors_module, "_select_joint_x_starts", inverted_x)
    application = apply_opening_representation_plan(building, shell, plan)

    assert application.anchors == []
    assert application.rejections[0].code == "architectural_order_not_preserved"
    assert application.shell.model_dump() == shell.model_dump()


def test_application_rejects_overlap_even_when_order_and_local_bounds_survive(monkeypatch):
    building, shell, plan = _fixture([
        _opening("left", 2.0),
        _opening("right", 3.8),
    ])

    monkeypatch.setattr(
        anchors_module,
        "_select_joint_z_starts",
        lambda **kwargs: {opening.id: raster.z_bricks for opening, raster, _ in kwargs["records"]},
    )

    def overlapping_x(**kwargs):
        records = kwargs["records"]
        starts = {opening.id: raster.x_studs for opening, raster, *_ in records}
        starts["left"] += 1
        starts["right"] -= 1
        return starts

    monkeypatch.setattr(anchors_module, "_select_joint_x_starts", overlapping_x)
    application = apply_opening_representation_plan(building, shell, plan)

    assert application.anchors == []
    assert application.adjustments == []
    assert application.rejections[0].code == "facade_layout_invalid"
    assert application.shell.model_dump() == shell.model_dump()


def test_successful_application_exposes_machine_readable_deltas_without_semantic_mutation():
    building, shell, plan = _fixture([_opening("opening", 2.0)])
    before = deepcopy(building.model_dump())

    first = apply_opening_representation_plan(building, shell, plan)
    second = apply_opening_representation_plan(building, shell, plan)

    assert building.model_dump() == before
    assert building.openings[0].type is OpeningType.UNKNOWN
    assert first.rejections == []
    assert first.adjustments
    assert first.model_dump()["adjustments"] == second.model_dump()["adjustments"]
    assert all(item.within_local_bounds for item in first.adjustments)
