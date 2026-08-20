from brickhouse.bricks.assembly import MAX_PARTS_PER_STEP, generate_assembly_plan
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart

def _model()->BrickModel:
    return BrickModel(building_id="b1",volume_id="v1",width_studs=8,depth_studs=6,height_plates=10,parts=[BrickModelPart(placement_id="wall-000002",part_id="BRICK_1X2",category="brick",component="wall",x_studs=2,y_studs=0,z_plates=0,rotation_quarter_turns=1,facade="front"),BrickModelPart(placement_id="wall-000001",part_id="BRICK_1X2",category="brick",component="wall",x_studs=0,y_studs=0,z_plates=0,rotation_quarter_turns=1,facade="front"),BrickModelPart(placement_id="wall-000003",part_id="BRICK_1X2",category="brick",component="wall",x_studs=0,y_studs=0,z_plates=3,rotation_quarter_turns=1,facade="front"),BrickModelPart(placement_id="roof-000001",part_id="BRICK_SLOPED_45_2X2",category="roof_tile",component="roof",x_studs=0,y_studs=0,z_plates=6,rotation_quarter_turns=0,roof_side="negative"),BrickModelPart(placement_id="roof-000002",part_id="TILE_1X2",category="ridge_tile",component="roof",x_studs=1,y_studs=0,z_plates=9,rotation_quarter_turns=0,roof_side="ridge")])
def test_plan_covers_every_part_exactly_once():
    m=_model();p=generate_assembly_plan(m);r=[pid for s in p.steps for pid in s.placement_ids];assert sorted(r)==sorted(x.placement_id for x in m.parts);assert len(r)==len(set(r))==p.total_parts
def test_walls_are_before_roof_and_levels_are_bottom_up():assert [(s.component,s.z_plates) for s in generate_assembly_plan(_model()).steps]==[("wall",0),("wall",3),("roof",6),("roof",9)]
def test_step_ids_sequences_and_part_order_are_deterministic():
    a=generate_assembly_plan(_model());b=generate_assembly_plan(_model());assert a==b;assert [s.step_id for s in a.steps]==["step-0001","step-0002","step-0003","step-0004"];assert a.steps[0].placement_ids==["wall-000001","wall-000002"]
def test_dense_level_is_split_into_short_practical_actions():
    parts=[BrickModelPart(placement_id=f"wall-{i:06d}",part_id="BRICK_1X1",category="brick",component="wall",x_studs=i,y_studs=0,z_plates=0,rotation_quarter_turns=0,facade="front") for i in range(MAX_PARTS_PER_STEP+5)]
    model=BrickModel(building_id="dense",volume_id="v1",width_studs=24,depth_studs=6,height_plates=3,parts=parts)
    plan=generate_assembly_plan(model)
    assert [len(step.placement_ids) for step in plan.steps]==[MAX_PARTS_PER_STEP,5]
    assert plan.steps[0].title.endswith("partie 1/2")
    assert plan.steps[1].title.endswith("partie 2/2")
