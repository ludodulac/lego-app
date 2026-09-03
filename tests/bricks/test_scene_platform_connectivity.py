from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_architecture import _scene_bounds
from brickhouse.bricks.scene_architecture_relations import _platform_representation_shifts
from brickhouse.bricks.scene_platform_connectivity import (
    _rooted_platform_pair_shifts,
    augment_brick_model_with_scene_platform_connectivity,
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


def _scene(platforms):
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "platform-connectivity",
            "name": "Generic connected platforms",
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
            "platforms": platforms,
            "appearance": {
                "walls": {"color": "off_white"},
                "roof": {"color": "dark_gray"},
                "frames": {"color": "dark_brown"},
            },
        }
    )


def _platform(platform_id, x, y, *, support=False):
    result = {
        "id": platform_id,
        "position": {"x": x, "y": y, "z": 1.0},
        "width": 0.2,
        "depth": 1.0,
        "thickness": 0.2,
        "material": "concrete",
        "source": SOURCE,
    }
    if support:
        result["supports"] = [
            {
                "id": f"{platform_id}-post",
                "position": {"x": x + 0.02, "y": y + 0.2, "z": 0.0},
                "width": 0.1,
                "depth": 0.1,
                "height": 0.8,
                "source": SOURCE,
            }
        ]
    return result


def _extra_shifts(scene):
    origin_x, origin_y, _ = _scene_bounds(scene)
    existing = _platform_representation_shifts(
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=5.0,
    )
    return _rooted_platform_pair_shifts(
        scene,
        existing,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=5.0,
    )


def test_rooted_platform_contact_closes_quantization_gap_and_moves_support():
    scene = _scene(
        [
            _platform("landing", -0.3, 2.0),
            _platform("extension", -0.6, 2.0, support=True),
        ]
    )
    source_before = scene.model_dump()

    assert _extra_shifts(scene)["extension"] == (1, 0)

    model = augment_brick_model_with_scene_platform_connectivity(
        _base_model(), scene, front_width_studs=50
    )
    landing = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-platform:landing:deck:")
    ]
    extension = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-platform:extension:deck:")
    ]
    supports = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-platform:extension:support1:")
    ]

    assert landing and extension and supports
    assert max(part.x_studs for part in extension) + 1 == min(part.x_studs for part in landing)
    assert min(part.x_studs for part in extension) == 1
    assert min(part.x_studs for part in supports) == 1
    assert scene.model_dump() == source_before


def test_floating_platform_only_component_is_not_given_an_arbitrary_root():
    scene = _scene(
        [
            _platform("first", -2.0, 2.0),
            _platform("second", -2.3, 2.0),
        ]
    )

    assert _extra_shifts(scene) == {"first": (0, 0), "second": (0, 0)}


def test_diagonal_tolerance_contact_is_not_reinterpreted_as_edge_contact():
    scene = _scene(
        [
            _platform("root", -0.3, 2.0),
            _platform("diagonal", -0.6, 0.9),
        ]
    )

    assert _extra_shifts(scene)["diagonal"] == (0, 0)
