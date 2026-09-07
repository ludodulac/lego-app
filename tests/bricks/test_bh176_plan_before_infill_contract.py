from brickhouse.building.models import (
    Appearance,
    BuildingModel,
    Facade,
    Metadata,
    Opening,
    OpeningType,
    OpeningVisualDescription,
    Position3D,
    SourceInfo,
    SourceKind,
    Volume,
    VolumeShape,
)
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.opening_plan_anchors import apply_opening_representation_plan
from brickhouse.bricks.opening_representation_plan import build_opening_representation_plan
from brickhouse.bricks.spatial import generate_spatial_brick_shell
from brickhouse.geometry import generate_building_geometry


def test_reserved_opening_footprint_exists_in_wall_grid_before_spatial_shell_generation():
    source = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)
    building = BuildingModel(
        schema_version="0.1",
        id="bh176-order",
        name="Ordering fixture",
        building_type="building",
        units="m",
        volumes=[Volume(
            id="main",
            shape=VolumeShape.RECTANGULAR_PRISM,
            position=Position3D(x=0, y=0, z=0),
            width=10,
            depth=7,
            height=6,
            floors=2,
            source=source,
        )],
        openings=[Opening(
            id="door",
            type=OpeningType.DOOR,
            volume_id="main",
            facade=Facade.FRONT,
            offset_horizontal=3.0,
            offset_vertical=0.0,
            width=1.6,
            height=2.0,
            source=source,
            opening_visual=OpeningVisualDescription(glazing="clear", leaf_count=2, pane_count=2),
        )],
        roofs=[],
        appearance=Appearance(),
        metadata=Metadata(created_from="synthetic"),
    )
    source_shell = generate_building_brick_shell(generate_building_geometry(building), 24)
    plan = build_opening_representation_plan(building, source_shell)
    reservation = plan.reservation("door")
    assert reservation.status == "reserved"

    application = apply_opening_representation_plan(building, source_shell, plan)
    front = next(wall for wall in application.shell.walls if wall.facade is Facade.FRONT)
    raster = next(item for item in front.grid.openings if item.id == "door")

    assert raster.width_studs == reservation.width_studs
    assert raster.height_bricks == reservation.height_bricks
    spatial = generate_spatial_brick_shell(application.shell)
    assert spatial.placements
