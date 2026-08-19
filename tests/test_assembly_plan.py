from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart

def _model()->BrickModel:
    return BrickModel(building_id="b1",volume_id="v1",width_studs=8,depth_studs=6,height_plates=10,parts=[BrickModelPart(placement_id="wall-000002",part_id="BRICK_1X2",category="brick",component="wall",x_studs=2,y_studs=0,z_plates=0,rotation_quarter_turns=1,facade="front"),BrickModelPart(placement_id="wall-000001",part_id="BRICK_1X2",category="brick",component="wall",x_studs=0,y_studs=0,z_plates=0,rotation_quarter_turns=1,facade="front"),BrickModelPart(placement_id="wall-000003",part_id="BRICK_1X2",category="brick",component="wall",x_studs=0,y_studs=0,z_plates=3,rotation_quarter_turns=1,facade="front"),BrickModelPart(placement_id="roof-000001",part_id="BRICK_SLOPED_45_2X2",category="roof_tile",component="roof",x_studs=0,y_studs=0,z_plates=6,rotation_quarter_turns=0,roof_side="negative"),BrickModelPart(placement_id="roof-000002",part_id="TILE_1X2",category="ridge_tile",component="roof",x_studs=1,y_studs=0,z_plates=9,rotation_quarter_turns=0,roof_side="ridge")])
def test_plan_covers_every_part_exactly_once():
    m=_model();p=generate_assembly_plan(m);r=[pid for s in p.steps for pid in s.placement_ids];assert sorted(r)==sorted(x.placement_id for x in m.parts);assert len(r)==len(set(r))==p.total_parts
def test_walls_are_before_roof_and_levels_are_bottom_up():assert [(s.component,s.z_plates) for s in generate_assembly_plan(_model()).steps]==[("wall",0),("wall",3),("roof",6),("roof",9)]
def test_step_ids_sequences_and_part_order_are_deterministic():
    a=generate_assembly_plan(_model());b=generate_assembly_plan(_model());assert a==b;assert [s.step_id for s in a.steps]==["step-0001","step-0002","step-0003","step-0004"];assert a.steps[0].placement_ids==["wall-000001","wall-000002"]
