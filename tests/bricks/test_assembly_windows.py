from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.building.models import Facade


def _part(pid, category, component, z=6):
    return BrickModelPart(
        placement_id=pid,
        part_id={
            "brick": "BRICK_1X2",
            "window_frame": "WINDOW_1X2X2_60592",
            "window_pane": "GLASS_FOR_WINDOW_1X2X2_60601",
            "facade_detail": "BRICK_1X1",
        }[category],
        category=category,
        component=component,
        x_studs=2,
        y_studs=0,
        z_plates=z,
        rotation_quarter_turns=0,
        facade=Facade.FRONT,
    )


def test_window_frame_and_pane_form_subassembly_before_facade_details():
    model = BrickModel(
        building_id="house",
        volume_id="main",
        width_studs=10,
        depth_studs=8,
        height_plates=18,
        parts=[
            _part("wall-1", "brick", "wall", 0),
            _part("pane-1", "window_pane", "facade_detail"),
            _part("detail-1", "facade_detail", "facade_detail"),
            _part("frame-1", "window_frame", "facade_detail"),
        ],
    )
    plan = generate_assembly_plan(model)
    assert [step.title for step in plan.steps] == [
        "Murs — façade avant — niveau 0 plates",
        "Assembler la fenêtre 1",
        "Détails de façade — niveau 6 plates",
    ]
    assert plan.steps[1].instruction_kind == "subassembly"
    assert plan.steps[1].placement_ids == ["frame-1", "pane-1"]
    assert [pid for step in plan.steps for pid in step.placement_ids] == [
        "wall-1", "frame-1", "pane-1", "detail-1"
    ]
