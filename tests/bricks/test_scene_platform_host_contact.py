from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_architecture import (
    _platform_host_contact_shift,
    augment_brick_model_with_scene_architecture,
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


def _scene(*, with_stair=False):
    stairs = []
    if with_stair:
        stairs.append(
            {
                "id": "run",
                "start": {"x": -0.3, "y": 1.0, "z": 0.0},
                "end": {"x": -0.3, "y": 2.0, "z": 1.0},
                "width": 0.01,
                "source": SOURCE,
            }
        )
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "platform-contact",
            "name": "Generic platform contact",
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
            "platforms": [
                {
                    "id": "landing",
                    "position": {"x": -0.3, "y": 2.0, "z": 1.0},
                    "width": 0.2,
                    "depth": 1.0,
                    "thickness": 0.2,
                    "material": "concrete",
                    "supports": [
                        {
                            "id": "post",
                            "position": {"x": -0.28, "y": 2.2, "z": 0.0},
                            "width": 0.1,
                            "depth": 0.1,
                            "height": 0.8,
                            "source": SOURCE,
                        }
                    ],
                    "source": SOURCE,
                }
            ],
            "stairs": stairs,
            "appearance": {
                "walls": {"color": "off_white"},
                "roof": {"color": "dark_gray"},
                "frames": {"color": "dark_brown"},
            },
        }
    )


def test_scene_valid_host_contact_closes_one_stud_quantization_gap():
    scene = _scene()
    platform = scene.platforms[0]
    source_before = scene.model_dump()

    shift = _platform_host_contact_shift(
        platform,
        scene,
        origin_x=-0.3,
        origin_y=0.0,
        studs_per_meter=5.0,
        width=1,
        depth=5,
    )
    assert shift == (1, 0)

    model = augment_brick_model_with_scene_architecture(
        _base_model(), scene, front_width_studs=50
    )
    deck = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-platform:landing:deck:")
    ]
    shifted_wall = next(part for part in model.parts if part.placement_id == "wall")

    assert scene.model_dump() == source_before
    assert deck
    assert {part.x_studs for part in deck} == {1}
    assert shifted_wall.x_studs == 2
    assert max(part.x_studs for part in deck) + 1 == shifted_wall.x_studs


def test_declared_support_moves_with_platform_representation_shift():
    scene = _scene()
    model = augment_brick_model_with_scene_architecture(
        _base_model(), scene, front_width_studs=50
    )
    deck = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-platform:landing:deck:")
    ]
    supports = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-platform:landing:support1:")
    ]

    assert deck
    assert supports
    assert min(part.x_studs for part in deck) == 1
    assert min(part.x_studs for part in supports) == 1


def test_existing_stair_connection_prevents_independent_platform_snap():
    scene = _scene(with_stair=True)
    platform = scene.platforms[0]

    shift = _platform_host_contact_shift(
        platform,
        scene,
        origin_x=-0.3,
        origin_y=0.9,
        studs_per_meter=5.0,
        width=1,
        depth=5,
    )
    assert shift == (0, 0)

    model = augment_brick_model_with_scene_architecture(
        _base_model(), scene, front_width_studs=50
    )
    deck = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-platform:landing:deck:")
    ]
    stair = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-stair:run:tread:")
    ]

    assert deck
    assert stair
    assert min(part.x_studs for part in deck) == 0
    assert {part.x_studs for part in stair} == {0}
