import pytest
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import generate_brick_model
from brickhouse.bricks.roof import GlobalRoofPlacement, SpatialRoof
from brickhouse.bricks.spatial import GlobalBrickPlacement, SpatialBrickShell
from brickhouse.building.models import Facade, RidgeDirection


def _shell():
    return SpatialBrickShell(
        building_id="house",
        volume_id="main",
        width_studs=10,
        depth_studs=8,
        height_bricks=2,
        placements=[
            GlobalBrickPlacement(brick_id="BRICK_1X4",facade=Facade.FRONT,x_studs=0,y_studs=0,z_plates=0,rotation_quarter_turns=1),
            GlobalBrickPlacement(brick_id="BRICK_1X4",facade=Facade.REAR,x_studs=0,y_studs=7,z_plates=0,rotation_quarter_turns=1),
            GlobalBrickPlacement(brick_id="BRICK_1X2",facade=Facade.LEFT,x_studs=0,y_studs=1,z_plates=3,rotation_quarter_turns=0),
        ],
    )


def _roof(building_id="house"):
    return SpatialRoof(
        building_id=building_id,
        roof_id="roof",
        ridge_direction=RidgeDirection.DEPTH,
        placements=[
            GlobalRoofPlacement(part_id="BRICK_SLOPED_45_2X4",side="negative",x_studs=0,y_studs=0,z_plates=6,rotation_quarter_turns=0),
            GlobalRoofPlacement(part_id="BRICK_SLOPED_45_2X4",side="positive",x_studs=8,y_studs=0,z_plates=6,rotation_quarter_turns=0),
            GlobalRoofPlacement(part_id="TILE_2X2",side="ridge",x_studs=4,y_studs=0,z_plates=9,rotation_quarter_turns=0),
        ],
    )


def test_brick_model_merges_wall_gable_and_roof_parts():
    model = generate_brick_model(_shell(), _roof())
    gables = [part for part in model.parts if part.placement_id.startswith("gable-")]
    assert gables
    assert sum(part.component == "wall" for part in model.parts) == 3 + len(gables)
    assert sum(part.component == "roof" for part in model.parts) == 3
    assert model.height_plates == 10


def test_gables_use_long_bricks_and_align_with_facade_planes():
    model = generate_brick_model(_shell(), _roof())
    gables = [part for part in model.parts if part.placement_id.startswith("gable-")]
    assert any(part.part_id != "BRICK_1X1" for part in gables)
    front = [part for part in gables if part.facade is Facade.FRONT]
    rear = [part for part in gables if part.facade is Facade.REAR]
    assert front and rear
    assert {part.y_studs for part in front} == {0}
    assert {part.y_studs for part in rear} == {7}
    assert min(part.x_studs for part in front) >= 2
    assert max(part.x_studs for part in front) <= 7


def test_brick_model_generates_stable_unique_ids_and_metadata():
    model = generate_brick_model(_shell(), _roof())
    ids = [part.placement_id for part in model.parts]
    assert ids[:3] == ["wall-000001", "wall-000002", "wall-000003"]
    assert ids[3] == "gable-000001"
    assert ids[-3:] == ["roof-000001", "roof-000002", "roof-000003"]
    assert len(ids) == len(set(ids))
    assert model.parts[0].facade is Facade.FRONT
    assert model.parts[-1].roof_side == "ridge"
    assert model.parts[-1].category == "ridge_tile"


def test_brick_model_rejects_building_mismatch():
    with pytest.raises(ValueError, match="same building"):
        generate_brick_model(_shell(), _roof(building_id="other"))


def test_brick_model_is_deterministic():
    assert generate_brick_model(_shell(), _roof()).model_dump(mode="json") == generate_brick_model(_shell(), _roof()).model_dump(mode="json")


def test_bom_aggregates_all_generated_parts_and_totals():
    model = generate_brick_model(_shell(), _roof())
    bom = generate_bom(model)
    quantities = {line.part_id: line.quantity for line in bom.lines}
    assert quantities["BRICK_1X4"] >= 2
    assert quantities["BRICK_1X2"] >= 1
    assert quantities["BRICK_SLOPED_45_2X4"] == 2
    assert quantities["TILE_2X2"] == 1
    assert bom.total_parts == len(model.parts)
    assert sum(quantities.values()) == len(model.parts)


def test_bom_order_and_serialization_are_deterministic():
    a = generate_bom(generate_brick_model(_shell(), _roof()))
    b = generate_bom(generate_brick_model(_shell(), _roof()))
    assert a.model_dump(mode="json") == b.model_dump(mode="json")
    assert [(line.category, line.part_id) for line in a.lines] == sorted((line.category, line.part_id) for line in a.lines)
