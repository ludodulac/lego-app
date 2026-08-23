from brickhouse.bricks.assembly import MAX_PARTS_PER_STEP, generate_assembly_plan
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart


def _model()->BrickModel:
    return BrickModel(building_id="b1",volume_id="v1",width_studs=8,depth_studs=6,height_plates=10,parts=[
        BrickModelPart(placement_id="wall-000002",part_id="BRICK_1X2",category="brick",component="wall",x_studs=2,y_studs=0,z_plates=0,rotation_quarter_turns=1,facade="front"),
        BrickModelPart(placement_id="wall-000001",part_id="BRICK_1X2",category="brick",component="wall",x_studs=0,y_studs=0,z_plates=0,rotation_quarter_turns=1,facade="front"),
        BrickModelPart(placement_id="wall-000003",part_id="BRICK_1X2",category="brick",component="wall",x_studs=0,y_studs=0,z_plates=3,rotation_quarter_turns=1,facade="front"),
        BrickModelPart(placement_id="roof-000001",part_id="BRICK_SLOPED_45_2X2",category="roof_tile",component="roof",x_studs=0,y_studs=0,z_plates=6,rotation_quarter_turns=0,roof_side="negative"),
        BrickModelPart(placement_id="roof-000002",part_id="TILE_1X2",category="ridge_tile",component="roof",x_studs=1,y_studs=0,z_plates=9,rotation_quarter_turns=0,roof_side="ridge")])


def test_plan_covers_every_part_exactly_once():
    m=_model();p=generate_assembly_plan(m);r=[pid for s in p.steps for pid in s.placement_ids]
    assert sorted(r)==sorted(x.placement_id for x in m.parts);assert len(r)==len(set(r))==p.total_parts


def test_walls_are_before_roof_and_levels_are_bottom_up():
    p=generate_assembly_plan(_model())
    assert [(s.component,s.z_plates) for s in p.steps]==[("wall",0),("wall",3),("roof",6),("roof",9)]
    assert [s.phase for s in p.steps]==["Structure","Structure","Toiture","Toiture"]
    assert p.total_bags==2


def test_step_ids_sequences_and_part_order_are_deterministic():
    a=generate_assembly_plan(_model());b=generate_assembly_plan(_model());assert a==b
    assert [s.step_id for s in a.steps]==["step-0001","step-0002","step-0003","step-0004"]
    assert a.steps[0].placement_ids==["wall-000001","wall-000002"]


def test_dense_level_is_split_into_short_practical_actions():
    parts=[BrickModelPart(placement_id=f"wall-{i:06d}",part_id="BRICK_1X1",category="brick",component="wall",x_studs=i,y_studs=0,z_plates=0,rotation_quarter_turns=0,facade="front") for i in range(MAX_PARTS_PER_STEP+5)]
    model=BrickModel(building_id="dense",volume_id="v1",width_studs=24,depth_studs=6,height_plates=3,parts=parts)
    plan=generate_assembly_plan(model)
    assert [len(step.placement_ids) for step in plan.steps]==[MAX_PARTS_PER_STEP,5]
    assert plan.steps[0].title.endswith("partie 1/2")
    assert plan.steps[1].title.endswith("partie 2/2")


def test_frame_and_pane_become_a_window_subassembly():
    parts=[
        BrickModelPart(placement_id="frame-1",part_id="WINDOW_1X2X2_60592",category="window_frame",component="facade_detail",x_studs=2,y_studs=0,z_plates=3,rotation_quarter_turns=1,facade="front"),
        BrickModelPart(placement_id="pane-1",part_id="GLASS_FOR_WINDOW_1X2X2_60601",category="window_pane",component="facade_detail",x_studs=2,y_studs=0,z_plates=3,rotation_quarter_turns=1,facade="front"),
    ]
    model=BrickModel(building_id="window",volume_id="v1",width_studs=8,depth_studs=6,height_plates=8,parts=parts)
    plan=generate_assembly_plan(model)
    assert plan.total_steps==1
    assert plan.total_bags==1
    step=plan.steps[0]
    assert step.instruction_kind=="subassembly"
    assert step.focus=="closeup"
    assert step.phase=="Fenêtres"
    assert step.placement_ids==["frame-1","pane-1"]


def test_scene_terrain_and_exterior_structures_get_distinct_build_phases():
    parts=[
        BrickModelPart(placement_id="scene-terrain:right:000001",part_id="BRICK_1X1",category="terrain",component="facade_detail",x_studs=0,y_studs=0,z_plates=0,rotation_quarter_turns=0,facade="right"),
        BrickModelPart(placement_id="wall-000001",part_id="BRICK_1X1",category="brick",component="wall",x_studs=1,y_studs=0,z_plates=3,rotation_quarter_turns=0,facade="front"),
        BrickModelPart(placement_id="scene-stair:run:tread:00001",part_id="BRICK_1X1",category="brick",component="facade_detail",x_studs=2,y_studs=0,z_plates=3,rotation_quarter_turns=0,facade="left"),
        BrickModelPart(placement_id="scene-platform:deck:board:00001",part_id="BRICK_1X4",category="timber",component="facade_detail",x_studs=3,y_studs=0,z_plates=6,rotation_quarter_turns=1,facade="left"),
    ]
    model=BrickModel(building_id="scene",volume_id="v1",width_studs=8,depth_studs=6,height_plates=12,parts=parts)
    plan=generate_assembly_plan(model)
    assert [step.phase for step in plan.steps]==["Terrain","Structure","Structures extérieures","Structures extérieures"]
    assert plan.total_bags==3
    assert plan.steps[0].title.startswith("Terrain")
