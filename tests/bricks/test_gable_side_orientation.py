from brickhouse.bricks.brick_model import generate_brick_model
from brickhouse.bricks.roof import GlobalRoofPlacement, SpatialRoof
from brickhouse.bricks.spatial import GlobalBrickPlacement, SpatialBrickShell
from brickhouse.building.models import Facade, RidgeDirection


def test_left_right_gable_infill_long_bricks_run_along_side_facade() -> None:
    shell = SpatialBrickShell(
        building_id="side-gable",
        volume_id="main",
        width_studs=10,
        depth_studs=8,
        height_bricks=2,
        placements=[
            GlobalBrickPlacement(
                brick_id="BRICK_1X4",
                facade=Facade.FRONT,
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=1,
            )
        ],
    )
    roof = SpatialRoof(
        building_id="side-gable",
        roof_id="roof",
        ridge_direction=RidgeDirection.WIDTH,
        placements=[
            GlobalRoofPlacement(
                part_id="BRICK_SLOPED_45_2X4",
                side="negative",
                x_studs=0,
                y_studs=0,
                z_plates=6,
                rotation_quarter_turns=1,
            ),
            GlobalRoofPlacement(
                part_id="BRICK_SLOPED_45_2X4",
                side="positive",
                x_studs=0,
                y_studs=6,
                z_plates=6,
                rotation_quarter_turns=1,
            ),
            GlobalRoofPlacement(
                part_id="TILE_2X2",
                side="ridge",
                x_studs=0,
                y_studs=3,
                z_plates=9,
                rotation_quarter_turns=1,
            ),
        ],
    )

    model = generate_brick_model(shell, roof)
    gables = [part for part in model.parts if part.placement_id.startswith("gable-")]
    assert gables
    assert {part.facade for part in gables} == {Facade.LEFT, Facade.RIGHT}
    long_parts = [part for part in gables if part.part_id != "BRICK_1X1"]
    assert long_parts
    assert all(part.rotation_quarter_turns == 0 for part in long_parts)
    assert {part.x_studs for part in gables if part.facade is Facade.LEFT} == {0}
    assert {part.x_studs for part in gables if part.facade is Facade.RIGHT} == {9}
