from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.export import create_export_bundle
from brickhouse.bricks.instructions import generate_instruction_plan


def _model() -> BrickModel:
    return BrickModel(
        building_id="instruction-test",
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
        ],
    )


def test_instruction_plan_is_lossless_projection_of_instruction_semantics() -> None:
    assembly = generate_assembly_plan(_model())
    instruction = generate_instruction_plan(assembly)

    assert instruction.building_id == assembly.building_id
    assert instruction.volume_id == assembly.volume_id
    assert instruction.total_steps == assembly.total_steps
    assert instruction.total_parts == assembly.total_parts
    assert [step.step_id for step in instruction.steps] == [step.step_id for step in assembly.steps]
    assert [step.sequence for step in instruction.steps] == [step.sequence for step in assembly.steps]
    assert [step.placement_ids for step in instruction.steps] == [step.placement_ids for step in assembly.steps]
    assert [step.view for step in instruction.steps] == [step.view for step in assembly.steps]
    assert [step.focus for step in instruction.steps] == [step.focus for step in assembly.steps]
    assert [step.instruction_kind for step in instruction.steps] == [step.instruction_kind for step in assembly.steps]
    assert [step.phase for step in instruction.steps] == [step.phase for step in assembly.steps]
    assert not hasattr(instruction.steps[0], "bag")


def test_export_bundle_adds_instruction_plan_without_removing_assembly_plan() -> None:
    model = _model()
    assembly = generate_assembly_plan(model)
    bundle = create_export_bundle(model, generate_bom(model), assembly)

    assert bundle.assembly_plan == assembly
    assert bundle.instruction_plan is not None
    assert bundle.instruction_plan.total_parts == len(model.parts)
    assert [step.placement_ids for step in bundle.instruction_plan.steps] == [
        step.placement_ids for step in assembly.steps
    ]
    assert [step.view for step in bundle.instruction_plan.steps] == [step.view for step in assembly.steps]
    assert any(step.instruction_kind == "subassembly" for step in bundle.instruction_plan.steps)
