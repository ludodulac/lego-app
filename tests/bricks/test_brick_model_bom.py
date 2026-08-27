import pytest
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart, generate_brick_model
from brickhouse.bricks.facade_details import FacadeDetailPlacement
from brickhouse.bricks.roof import GlobalRoofPlacement, SpatialRoof
from brickhouse.bricks.spatial import GlobalBrickPlacement, SpatialBrickShell
from brickhouse.building.models import Facade, RidgeDirection


def _shell():
    return SpatialBrickShell(building_id="house",volume_id="main",width_studs=10,depth_studs=8,height_bricks=2,placements=[GlobalBrickPlacement(brick_id="BRICK_1X4",facade=Facade.FRONT,x_studs=0,y_studs=0,z_plates=0,rotation_quarter_turns=1),GlobalBrickPlacement(brick_id="BRICK_1X4",facade=Facade.REAR,x_studs=0,y_studs=7,z_plates=0,rotation_quarter_turns=1),GlobalBrickPlacement(brick_id="BRICK_1X2",facade=Facade.LEFT,x_studs=0,y_studs=1,z_plates=3,rotation_quarter_turns=0)])

def _roof(building_id="house"):
    return SpatialRoof(building_id=building_id,roof_id="roof",ridge_direction=RidgeDirection.DEPTH,placements=[GlobalRoofPlacement(part_id="BRICK_SLOPED_45_2X4",side="negative",x_studs=0,y_studs=0,z_plates=6,rotation_quarter_turns=0),GlobalRoofPlacement(part_id="BRICK_SLOPED_45_2X4",side="positive",x_studs=8,y_studs=0,z_plates=6,rotation_quarter_turns=0),GlobalRoofPlacement(part_id="TILE_2X2",side="ridge",x_studs=4,y_studs=0,z_plates=9,rotation_quarter_turns=0)])

def test_brick_model_merges_wall_gable_and_roof_parts():
    model=generate_brick_model(_shell(),_roof()); gables=[p for p in model.parts if p.placement_id.startswith("gable-")]
    assert gables
    assert sum(p.component=="wall" for p in model.parts)==3+len(gables)
    assert sum(p.component=="roof" for p in model.parts)==3
    assert model.height_plates==10

def test_gables_use_long_bricks_align_and_reach_roof_connection_zone():
    model=generate_brick_model(_shell(),_roof()); gables=[p for p in model.parts if p.placement_id.startswith("gable-")]
    assert any(p.part_id!="BRICK_1X1" for p in gables)
    front=[p for p in gables if p.facade is Facade.FRONT]; rear=[p for p in gables if p.facade is Facade.REAR]
    assert front and rear
    assert {p.y_studs for p in front}=={0}; assert {p.y_studs for p in rear}=={7}
    assert min(p.x_studs for p in front)==1
    assert max(p.x_studs for p in front)<=8

def test_brick_model_generates_stable_unique_ids_and_metadata():
    model=generate_brick_model(_shell(),_roof()); ids=[p.placement_id for p in model.parts]
    assert ids[:3]==["wall-000001","wall-000002","wall-000003"]
    assert ids[3]=="gable-000001"; assert ids[-3:]==["roof-000001","roof-000002","roof-000003"]
    assert len(ids)==len(set(ids)); assert model.parts[0].facade is Facade.FRONT
    assert model.parts[-1].roof_side=="ridge"; assert model.parts[-1].category=="ridge_tile"

def test_facade_trim_provenance_and_semantic_color_survive_brick_model_conversion():
    detail = FacadeDetailPlacement(
        part_id="BRICK_1X4",
        category="masonry",
        facade=Facade.FRONT,
        x_studs=2,
        y_studs=0,
        z_plates=6,
        rotation_quarter_turns=1,
        opening_id="window-front-1",
        trim_role="head",
        semantic_color="slightly darker beige",
    )
    model = generate_brick_model(_shell(), None, facade_details=[detail])
    generated = next(part for part in model.parts if part.placement_id == "detail-000001")

    assert generated.opening_id == "window-front-1"
    assert generated.trim_role == "head"
    assert generated.category == "masonry"
    assert generated.semantic_color == "slightly darker beige"
    dumped = generated.model_dump(mode="json")
    assert dumped["opening_id"] == "window-front-1"
    assert dumped["trim_role"] == "head"
    assert dumped["semantic_color"] == "slightly darker beige"


def test_trim_role_requires_facade_detail_opening_provenance():
    with pytest.raises(ValueError, match="trim_role requires opening_id"):
        BrickModelPart(
            placement_id="detail-test",
            part_id="BRICK_1X1",
            category="facade_detail",
            component="facade_detail",
            x_studs=0,
            y_studs=0,
            z_plates=0,
            rotation_quarter_turns=0,
            facade=Facade.FRONT,
            trim_role="sill",
        )


def test_semantic_color_is_rejected_outside_facade_detail_evidence_zone():
    with pytest.raises(ValueError, match="semantic_color"):
        BrickModelPart(
            placement_id="wall-colored",
            part_id="BRICK_1X1",
            category="brick",
            component="wall",
            x_studs=0,
            y_studs=0,
            z_plates=0,
            rotation_quarter_turns=0,
            facade=Facade.FRONT,
            semantic_color="beige",
        )


def test_brick_model_rejects_building_mismatch():
    with pytest.raises(ValueError,match="same building"): generate_brick_model(_shell(),_roof(building_id="other"))

def test_brick_model_is_deterministic():
    assert generate_brick_model(_shell(),_roof()).model_dump(mode="json")==generate_brick_model(_shell(),_roof()).model_dump(mode="json")

def test_bom_aggregates_all_generated_parts_and_totals():
    model=generate_brick_model(_shell(),_roof()); bom=generate_bom(model); quantities={line.part_id:line.quantity for line in bom.lines}
    assert quantities["BRICK_1X4"]>=2; assert quantities["BRICK_1X2"]>=1
    assert quantities["BRICK_SLOPED_45_2X4"]==2; assert quantities["TILE_2X2"]==1
    assert bom.total_parts==len(model.parts); assert sum(quantities.values())==len(model.parts)


def test_bom_keeps_same_part_and_category_separate_when_semantic_colors_differ():
    base = dict(
        part_id="BRICK_1X1",
        category="masonry",
        component="facade_detail",
        x_studs=0,
        y_studs=0,
        z_plates=0,
        rotation_quarter_turns=0,
        facade=Facade.FRONT,
        opening_id="w1",
        trim_role="head",
    )
    model = BrickModel(
        building_id="house",
        volume_id="main",
        width_studs=4,
        depth_studs=4,
        height_plates=3,
        parts=[
            BrickModelPart(placement_id="a", semantic_color="beige", **base),
            BrickModelPart(placement_id="b", semantic_color="gray", **base),
            BrickModelPart(placement_id="c", semantic_color="beige", **base),
        ],
    )
    bom = generate_bom(model)

    assert [(line.semantic_color, line.quantity) for line in bom.lines] == [
        ("beige", 2),
        ("gray", 1),
    ]
    assert bom.unique_part_types == 2
    assert bom.total_parts == 3


def test_bom_order_and_serialization_are_deterministic():
    a=generate_bom(generate_brick_model(_shell(),_roof())); b=generate_bom(generate_brick_model(_shell(),_roof()))
    assert a.model_dump(mode="json")==b.model_dump(mode="json")
    keys=[(line.category,line.part_id,line.semantic_color or "") for line in a.lines]
    assert keys==sorted(keys)
