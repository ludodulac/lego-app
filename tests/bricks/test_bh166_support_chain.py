import copy

import pytest

from brickhouse.building import Facade
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.piece_capabilities import (
    PieceCapability,
    PieceCapabilityRegistry,
    PieceCapabilityStage,
    validate_model_part_capabilities,
)
from brickhouse.bricks.support_chain import (
    analyze_standard_brick_support_chain,
    validate_standard_brick_support_chain,
)


def _part(placement_id, part_id, *, x, y, z, rotation=0):
    return BrickModelPart(
        placement_id=placement_id,
        part_id=part_id,
        category="brick",
        component="wall",
        x_studs=x,
        y_studs=y,
        z_plates=z,
        rotation_quarter_turns=rotation,
        facade=Facade.FRONT,
    )


def _model(parts):
    return BrickModel(
        building_id="generic-support",
        volume_id="v",
        width_studs=20,
        depth_studs=20,
        height_plates=30,
        parts=parts,
    )


def test_vertical_stack_reaches_ground_transitively():
    model = _model([
        _part("base", "BRICK_2X2", x=0, y=0, z=0),
        _part("middle", "BRICK_2X2", x=0, y=0, z=3),
        _part("top", "BRICK_1X2", x=1, y=0, z=6),
    ])
    report = analyze_standard_brick_support_chain(model)
    assert report.valid is True
    top = next(node for node in report.nodes if node.placement_id == "top")
    assert top.supporters == ["middle"]
    assert top.reaches_ground is True
    validate_standard_brick_support_chain(model)


def test_rotated_footprint_is_used_for_real_stud_overlap():
    model = _model([
        _part("base", "BRICK_1X4", x=0, y=0, z=0, rotation=1),
        _part("upper", "BRICK_1X2", x=3, y=0, z=3),
    ])
    report = analyze_standard_brick_support_chain(model)
    assert report.valid is True
    upper = next(node for node in report.nodes if node.placement_id == "upper")
    assert upper.supporters == ["base"]


def test_bridging_brick_needs_at_least_one_actual_supporting_stud():
    supported = _model([
        _part("pier", "BRICK_1X1", x=2, y=0, z=0),
        _part("beam", "BRICK_1X4", x=0, y=0, z=3, rotation=1),
    ])
    assert analyze_standard_brick_support_chain(supported).valid is True

    floating = _model([
        _part("pier", "BRICK_1X1", x=4, y=0, z=0),
        _part("beam", "BRICK_1X4", x=0, y=0, z=3, rotation=1),
    ])
    report = analyze_standard_brick_support_chain(floating)
    assert report.valid is False
    assert report.unsupported_placement_ids == ["beam"]


def test_floating_chain_does_not_become_valid_by_supporting_itself_above_ground():
    model = _model([
        _part("floating-base", "BRICK_2X2", x=5, y=5, z=6),
        _part("floating-top", "BRICK_2X2", x=5, y=5, z=9),
    ])
    report = analyze_standard_brick_support_chain(model)
    assert report.unsupported_placement_ids == ["floating-base", "floating-top"]
    with pytest.raises(ValueError, match="continuous stud/tube support chain to ground"):
        validate_standard_brick_support_chain(model)


def test_noncanonical_parts_are_not_claimed_by_this_first_support_slice():
    model = _model([
        _part("ground", "BRICK_1X1", x=0, y=0, z=0),
        BrickModelPart(
            placement_id="window-pane",
            part_id="GLASS_FOR_WINDOW_1X2X2_60601",
            category="window_pane",
            component="facade_detail",
            x_studs=10,
            y_studs=0,
            z_plates=12,
            rotation_quarter_turns=0,
            facade=Facade.FRONT,
        ),
    ])
    report = analyze_standard_brick_support_chain(model)
    assert report.audited_placement_ids == ["ground"]
    assert report.valid is True


def test_report_is_deterministic_and_does_not_mutate_model():
    parts = [
        _part("z-top", "BRICK_1X1", x=0, y=0, z=3),
        _part("a-base", "BRICK_1X2", x=0, y=0, z=0),
    ]
    model = _model(parts)
    before = copy.deepcopy(model.model_dump())
    first = analyze_standard_brick_support_chain(model).model_dump()
    second = analyze_standard_brick_support_chain(model).model_dump()
    assert first == second
    assert model.model_dump() == before


def test_existing_placement_capability_gate_rejects_a_floating_canonical_brick():
    registry = PieceCapabilityRegistry(
        pieces=[
            PieceCapability(
                engine_id="BRICK_1X1",
                name="1x1 brick",
                category="brick",
                stage=PieceCapabilityStage.PLACEMENT_APPROVED,
            )
        ]
    )
    model = _model([_part("floating", "BRICK_1X1", x=0, y=0, z=3)])
    with pytest.raises(ValueError, match="continuous stud/tube support chain to ground"):
        validate_model_part_capabilities(model, registry)
