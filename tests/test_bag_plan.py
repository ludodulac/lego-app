from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.bags import generate_bag_plan
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.export import create_export_bundle


def _model() -> BrickModel:
    return BrickModel(
        building_id="bag-test",
        volume_id="v1",
        width_studs=8,
        depth_studs=6,
        height_plates=12,
        parts=[
            BrickModelPart(
                placement_id="wall-front-1",
                part_id="BRICK_1X2",
                category="brick",
                component="wall",
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                facade="front",
            ),
            BrickModelPart(
                placement_id="frame-1",
                part_id="WINDOW_1X2X2_60592",
                category="window_frame",
                component="facade_detail",
                x_studs=2,
                y_studs=0,
                z_plates=3,
                rotation_quarter_turns=1,
                facade="front",
            ),
            BrickModelPart(
                placement_id="pane-1",
                part_id="GLASS_FOR_WINDOW_1X2X2_60601",
                category="window_pane",
                component="facade_detail",
                x_studs=2,
                y_studs=0,
                z_plates=3,
                rotation_quarter_turns=1,
                facade="front",
            ),
            BrickModelPart(
                placement_id="detail-1",
                part_id="BRICK_1X1",
                category="facade_detail",
                component="facade_detail",
                x_studs=4,
                y_studs=0,
                z_plates=6,
                rotation_quarter_turns=0,
                facade="front",
            ),
        ],
    )


def test_bag_plan_preserves_current_assembly_grouping_and_order() -> None:
    assembly = generate_assembly_plan(_model())
    bag_plan = generate_bag_plan(assembly)

    assert bag_plan.building_id == assembly.building_id
    assert bag_plan.volume_id == assembly.volume_id
    assert bag_plan.total_bags == assembly.total_bags
    assert bag_plan.total_parts == assembly.total_parts
    assert [bag.bag_number for bag in bag_plan.bags] == list(range(1, assembly.total_bags + 1))

    assert [step_id for bag in bag_plan.bags for step_id in bag.assembly_step_ids] == [
        step.step_id for step in assembly.steps
    ]
    assert [placement_id for bag in bag_plan.bags for placement_id in bag.placement_ids] == [
        placement_id for step in assembly.steps for placement_id in step.placement_ids
    ]

    for bag in bag_plan.bags:
        underlying = [step for step in assembly.steps if step.bag == bag.bag_number]
        assert bag.phases == list(dict.fromkeys(step.phase for step in underlying))


def test_export_bundle_adds_bag_plan_without_removing_existing_bag_field() -> None:
    model = _model()
    assembly = generate_assembly_plan(model)
    bundle = create_export_bundle(model, generate_bom(model), assembly)

    assert bundle.assembly_plan == assembly
    assert bundle.instruction_plan is not None
    assert all(not hasattr(step, "bag") for step in bundle.instruction_plan.steps)
    assert bundle.bag_plan is not None
    assert bundle.bag_plan.total_bags == assembly.total_bags
    assert bundle.bag_plan.total_parts == len(model.parts)
    assert [step_id for bag in bundle.bag_plan.bags for step_id in bag.assembly_step_ids] == [
        step.step_id for step in assembly.steps
    ]
