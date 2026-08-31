from brickhouse.bricks.brick_model import generate_brick_model
from brickhouse.bricks.roof import GlobalRoofPlacement, SpatialRoof
from brickhouse.bricks.spatial import GlobalBrickPlacement, SpatialBrickShell
from brickhouse.building.models import Facade, RidgeDirection


def _shell() -> SpatialBrickShell:
    return SpatialBrickShell(
        building_id="real-house-5",
        volume_id="volume_main",
        width_studs=48,
        depth_studs=40,
        height_bricks=13,
        placements=[
            GlobalBrickPlacement(
                brick_id="BRICK_1X8",
                facade=Facade.FRONT,
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=1,
            ),
            GlobalBrickPlacement(
                brick_id="BRICK_1X8",
                facade=Facade.REAR,
                x_studs=0,
                y_studs=39,
                z_plates=0,
                rotation_quarter_turns=1,
            ),
        ],
    )


def _roof() -> SpatialRoof:
    wall_top = 39
    placements = []
    # Real-house-5 uses the shallow 18-degree family at medium scale.
    # Its physical footprint is 4 studs while the course advance is 3.
    for course, axis in enumerate(range(0, 24, 3)):
        z = wall_top + course * 3
        placements.append(
            GlobalRoofPlacement(
                part_id="BRICK_SLOPED_18_4X2",
                side="negative",
                x_studs=axis,
                y_studs=0,
                z_plates=z,
                rotation_quarter_turns=0,
            )
        )
        placements.append(
            GlobalRoofPlacement(
                part_id="BRICK_SLOPED_18_4X2",
                side="positive",
                x_studs=48 - 4 - axis,
                y_studs=0,
                z_plates=z,
                rotation_quarter_turns=0,
            )
        )
    placements.append(
        GlobalRoofPlacement(
            part_id="TILE_2X2",
            side="ridge",
            x_studs=23,
            y_studs=0,
            z_plates=wall_top + 8 * 3,
            rotation_quarter_turns=0,
        )
    )
    return SpatialRoof(
        building_id="real-house-5",
        roof_id="roof_main",
        ridge_direction=RidgeDirection.DEPTH,
        placements=placements,
    )


def test_real_house_5_shallow_gable_clears_full_18_degree_slope_footprint() -> None:
    model = generate_brick_model(_shell(), _roof())
    front = [
        part
        for part in model.parts
        if part.placement_id.startswith("gable-") and part.facade is Facade.FRONT
    ]
    assert front

    first_course = [part for part in front if part.z_plates == 39]
    second_course = [part for part in front if part.z_plates == 42]
    assert first_course and second_course

    # The old course-advance rule would have started at x=3, inside the
    # 4-stud solid footprint of the eave slope. The corrected rule starts at 4.
    assert min(part.x_studs for part in first_course) == 4
    assert max(part.x_studs for part in first_course) <= 43
    assert min(part.x_studs for part in second_course) == 7


def test_real_house_5_clearance_does_not_change_architectural_scale() -> None:
    model = generate_brick_model(_shell(), _roof())
    assert model.width_studs == 48
    assert model.depth_studs == 40
