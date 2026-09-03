from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_architecture import augment_brick_model_with_scene_architecture, _scene_bounds
from brickhouse.bricks.scene_architecture_relations import (
    _platform_representation_shifts,
    _safe_stair_endpoint_shifts,
    _volume_endpoint_shift,
    augment_brick_model_with_scene_architecture_relations,
)
from brickhouse.building.models import Facade
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.8}


def _base_model():
    return BrickModel(
        building_id="house",
        volume_id="main",
        width_studs=50,
        depth_studs=40,
        height_plates=60,
        parts=[
            BrickModelPart(
                placement_id="wall",
                part_id="BRICK_1X1",
                category="brick",
                component="wall",
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                facade=Facade.LEFT,
            )
        ],
    )


def _scene(*, unsafe_perpendicular=False):
    if unsafe_perpendicular:
        start = {"x": -1.0, "y": -0.1, "z": 0.0}
        end = {"x": 0.5, "y": -0.1, "z": 1.0}
    else:
        start = {"x": -1.1, "y": 2.0, "z": 0.0}
        end = {"x": -0.1, "y": 2.0, "z": 1.0}
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "direct-stair-boundary",
            "name": "Generic direct stair boundary contact",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "width": {"value": 10, "source": SOURCE},
                    "depth": {"value": 8, "source": SOURCE},
                    "height": {"value": 6, "source": SOURCE},
                    "floors": 2,
                    "source": SOURCE,
                }
            ],
            "stairs": [
                {
                    "id": "run",
                    "start": start,
                    "end": end,
                    "width": 0.01,
                    "material": "concrete",
                    "source": SOURCE,
                }
            ],
            "appearance": {
                "walls": {"color": "off_white"},
                "roof": {"color": "dark_gray"},
                "frames": {"color": "dark_brown"},
            },
        }
    )


def _relation_context(scene):
    origin_x, origin_y, _ = _scene_bounds(scene)
    shifts = _platform_representation_shifts(
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=5.0,
    )
    return origin_x, origin_y, shifts


def test_scene_valid_direct_boundary_contact_closes_one_stud_gap():
    scene = _scene()
    stair = scene.stairs[0]
    origin_x, origin_y, shifts = _relation_context(scene)

    assert _volume_endpoint_shift(
        stair.end,
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=5.0,
    ) == (1, 0)
    assert _safe_stair_endpoint_shifts(
        stair,
        scene,
        shifts,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=5.0,
    ) == ((0, 0), (1, 0))

    historical = augment_brick_model_with_scene_architecture(
        _base_model(), scene, front_width_studs=50
    )
    result = augment_brick_model_with_scene_architecture_relations(
        _base_model(), scene, front_width_studs=50
    )
    historical_treads = [
        part for part in historical.parts
        if part.placement_id.startswith("scene-stair:run:tread:")
    ]
    treads = [
        part for part in result.parts
        if part.placement_id.startswith("scene-stair:run:tread:")
    ]
    shifted_wall = next(part for part in result.parts if part.placement_id == "wall")

    assert max(part.x_studs for part in historical_treads) + 1 == shifted_wall.x_studs
    assert max(part.x_studs for part in treads) == shifted_wall.x_studs
    assert len({part.y_studs for part in treads}) == 1


def test_perpendicular_direct_boundary_snap_is_dropped_instead_of_bending_run():
    scene = _scene(unsafe_perpendicular=True)
    stair = scene.stairs[0]
    origin_x, origin_y, shifts = _relation_context(scene)

    proposed = _volume_endpoint_shift(
        stair.end,
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=5.0,
    )
    assert proposed == (0, 1)
    assert _safe_stair_endpoint_shifts(
        stair,
        scene,
        shifts,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=5.0,
    ) == ((0, 0), (0, 0))

    result = augment_brick_model_with_scene_architecture_relations(
        _base_model(), scene, front_width_studs=50
    )
    treads = [
        part for part in result.parts
        if part.placement_id.startswith("scene-stair:run:tread:")
    ]
    assert treads
    assert len({part.y_studs for part in treads}) == 1


def test_direct_boundary_anchor_keeps_source_and_vertical_geometry_immutable():
    scene = _scene()
    source_before = scene.model_dump()
    historical = augment_brick_model_with_scene_architecture(
        _base_model(), scene, front_width_studs=50
    )
    result = augment_brick_model_with_scene_architecture_relations(
        _base_model(), scene, front_width_studs=50
    )
    historical_treads = [
        part for part in historical.parts
        if part.placement_id.startswith("scene-stair:run:tread:")
    ]
    treads = [
        part for part in result.parts
        if part.placement_id.startswith("scene-stair:run:tread:")
    ]
    body = [
        part for part in result.parts
        if part.placement_id.startswith("scene-stair:run:body:")
    ]

    assert scene.model_dump() == source_before
    assert treads and body
    assert max(part.z_plates for part in treads) == max(part.z_plates for part in historical_treads)
    terminal_x = max(part.x_studs for part in treads)
    terminal_z = max(part.z_plates for part in treads if part.x_studs == terminal_x)
    assert any(part.x_studs == terminal_x and part.z_plates < terminal_z for part in body)
    assert all(part.placement_id.startswith("scene-stair:run:") for part in [*treads, *body])
