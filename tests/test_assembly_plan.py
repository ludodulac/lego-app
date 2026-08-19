from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart


def _model() -> BrickModel:
    return BrickModel(
        building_id="b1",
        volume_id="v1",
        width_studs=8,
        depth_studs=6,
        height_plates=10,
        parts=[
            BrickModelPart(placement_id="wall-000002", part_id="BRICK_1X2", category="brick", component="wall", x_studs=2, y_studs=0, z_plates=0, rotation_quarter_turns=1, facade="front"),
            BrickModelPart(placement_id="wall-000001", part_id="BRICK_1X2", category="brick", component="wall", x_studs=0, y_studs=0, z_plates=0, rotation_quarter_turns=1, facade="front"),
            BrickModelPart(placement_id="wall-000003", part_id="BRICK_1X2", category="brick", component="wall", x_studs=0, y_studs=0, z_plates=3, rotation_quarter_turns=1, facade="front"),
            BrickModelPart(placement_id="roof-000001", part_id="ROOF_TILE_1X2", category="roof_tile", component="roof", x_studs=0, y_studs=0, z_plates=6, rotation_quarter_turns=0, roof_side="negative"),
            BrickModelPart(placement_id="roof-000002", part_id="RIDGE_TILE_1X2", category="ridge_tile", component="roof", x_studs=1, y_studs=0, z_plates=9, rotation_quarter_turns=0, roof_side="ridge"),
        ],
    )


def test_plan_covers_every_part_exactly_once():
    model = _model()
    plan = generate_assembly_plan(model)
    referenced = [pid for step in plan.steps for pid in step.placement_ids]
    assert sorted(referenced) == sorted(part.placement_id for part in model.parts)
    assert len(referenced) == len(set(referenced)) == plan.total_parts


def test_walls_are_before_roof_and_levels_are_bottom_up():
    plan = generate_assembly_plan(_model())
    assert [(step.component, step.z_plates) for step in plan.steps] == [
        ("wall", 0),
        ("wall", 3),
        ("roof", 6),
        ("roof", 9),
    ]


def test_step_ids_sequences_and_part_order_are_deterministic():
    first = generate_assembly_plan(_model())
    second = generate_assembly_plan(_model())
    assert first == second
    assert [step.step_id for step in first.steps] == ["step-0001", "step-0002", "step-0003", "step-0004"]
    assert first.steps[0].placement_ids == ["wall-000001", "wall-000002"]
