import pytest
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import generate_brick_model
from brickhouse.bricks.roof import GlobalRoofPlacement, SpatialRoof
from brickhouse.bricks.spatial import GlobalBrickPlacement, SpatialBrickShell
from brickhouse.building.models import Facade, RidgeDirection

def _shell():
    return SpatialBrickShell(building_id="house",volume_id="main",width_studs=10,depth_studs=8,height_bricks=2,placements=[GlobalBrickPlacement(brick_id="BRICK_1X4",facade=Facade.FRONT,x_studs=0,y_studs=0,z_plates=0,rotation_quarter_turns=1),GlobalBrickPlacement(brick_id="BRICK_1X4",facade=Facade.REAR,x_studs=0,y_studs=7,z_plates=0,rotation_quarter_turns=1),GlobalBrickPlacement(brick_id="BRICK_1X2",facade=Facade.LEFT,x_studs=0,y_studs=1,z_plates=3,rotation_quarter_turns=0)])
def _roof(building_id="house"):
    return SpatialRoof(building_id=building_id,roof_id="roof",ridge_direction=RidgeDirection.DEPTH,placements=[GlobalRoofPlacement(part_id="BRICK_SLOPED_45_2X4",side="negative",x_studs=0,y_studs=0,z_plates=6,rotation_quarter_turns=0),GlobalRoofPlacement(part_id="BRICK_SLOPED_45_2X4",side="positive",x_studs=8,y_studs=0,z_plates=6,rotation_quarter_turns=0),GlobalRoofPlacement(part_id="TILE_2X2",side="ridge",x_studs=4,y_studs=0,z_plates=9,rotation_quarter_turns=0)])
def test_brick_model_merges_wall_and_roof_parts():
    m=generate_brick_model(_shell(),_roof());assert len(m.parts)==6;assert sum(p.component=="wall" for p in m.parts)==3;assert sum(p.component=="roof" for p in m.parts)==3;assert m.height_plates==10
def test_brick_model_generates_stable_unique_ids_and_metadata():
    m=generate_brick_model(_shell(),_roof());assert [p.placement_id for p in m.parts]==["wall-000001","wall-000002","wall-000003","roof-000001","roof-000002","roof-000003"];assert m.parts[0].facade is Facade.FRONT;assert m.parts[-1].roof_side=="ridge";assert m.parts[-1].category=="ridge_tile"
def test_brick_model_rejects_building_mismatch():
    with pytest.raises(ValueError,match="same building"):generate_brick_model(_shell(),_roof(building_id="other"))
def test_brick_model_is_deterministic():assert generate_brick_model(_shell(),_roof()).model_dump(mode="json")==generate_brick_model(_shell(),_roof()).model_dump(mode="json")
def test_bom_aggregates_canonical_parts_and_totals():
    b=generate_bom(generate_brick_model(_shell(),_roof()));q={l.part_id:l.quantity for l in b.lines};assert q["BRICK_1X4"]==2;assert q["BRICK_1X2"]==1;assert q["BRICK_SLOPED_45_2X4"]==2;assert q["TILE_2X2"]==1;assert b.total_parts==6;assert b.unique_part_types==4
def test_bom_order_and_serialization_are_deterministic():
    a=generate_bom(generate_brick_model(_shell(),_roof()));b=generate_bom(generate_brick_model(_shell(),_roof()));assert a.model_dump(mode="json")==b.model_dump(mode="json");assert [(l.category,l.part_id) for l in a.lines]==sorted((l.category,l.part_id) for l in a.lines)
