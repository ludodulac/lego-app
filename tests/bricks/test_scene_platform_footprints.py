from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_architecture import (
    _scene_bounds,
    augment_brick_model_with_scene_architecture,
)
from brickhouse.bricks.scene_platform_footprints import select_platform_footprint
from brickhouse.building.models import Facade
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.9}


def _prop(value):
    return {"value": value, "source": SOURCE, "evidence": []}


def _scene(*, supports=None, second_platform=False):
    platform = {
        "id": "deck",
        "position": {"x": -0.26, "y": 1.0, "z": 1.0},
        "width": 0.26,
        "depth": 1.0,
        "thickness": 0.2,
        "material": "concrete",
        "supports": supports or [],
        "source": SOURCE,
    }
    platforms = [platform]
    if second_platform:
        platforms.append(
            {
                "id": "neighbor",
                "position": {"x": -0.52, "y": 1.0, "z": 1.0},
                "width": 0.26,
                "depth": 1.0,
                "thickness": 0.2,
                "material": "concrete",
                "source": SOURCE,
            }
        )
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "generic-platform-footprints",
            "name": "Generic platform footprints",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "width": _prop(8.0),
                    "depth": _prop(6.0),
                    "height": _prop(4.0),
                    "floors": 1,
                    "source": SOURCE,
                }
            ],
            "platforms": platforms,
            "appearance": {},
        }
    )


def _base_model():
    return BrickModel(
        building_id="generic-platform-footprints",
        volume_id="main",
        width_studs=32,
        depth_studs=24,
        height_plates=48,
        parts=[
            BrickModelPart(
                placement_id="seed",
                part_id="BRICK_1X1",
                category="brick",
                component="wall",
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                facade=Facade.FRONT,
            )
        ],
    )


def _select(scene):
    origin_x, origin_y, _ = _scene_bounds(scene)
    return select_platform_footprint(
        scene.platforms[0],
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=4.0,
    )


def test_free_platform_prefers_nearest_proportional_footprint_over_outward_ceil():
    scene = _scene()
    before = scene.model_dump(mode="json", by_alias=True)

    solution = _select(scene)

    assert solution.target_width_studs == 1.04
    assert (solution.width_studs, solution.depth_studs) == (1, 4)
    assert not solution.used_legacy_fallback
    assert scene.model_dump(mode="json", by_alias=True) == before


def test_declared_support_can_force_conservative_outward_footprint():
    scene = _scene(
        supports=[
            {
                "position": {"x": -0.05, "y": 1.0, "z": 0.0},
                "width": 0.05,
                "depth": 0.2,
                "height": 1.0,
                "source": SOURCE,
            }
        ]
    )

    solution = _select(scene)

    assert (solution.width_studs, solution.depth_studs) == (2, 4)
    assert solution.used_legacy_fallback


def test_platform_contact_keeps_legacy_footprint_until_joint_contact_solve():
    scene = _scene(second_platform=True)

    solution = _select(scene)

    assert (solution.width_studs, solution.depth_studs) == (2, 4)
    assert solution.used_legacy_fallback


def test_renderer_consumes_the_selected_platform_footprint():
    scene = _scene()

    rendered = augment_brick_model_with_scene_architecture(
        _base_model(),
        scene,
        front_width_studs=32,
    )
    deck = [
        part
        for part in rendered.parts
        if part.placement_id.startswith("scene-platform:deck:deck:")
    ]

    assert deck
    assert len({part.x_studs for part in deck}) == 1
    assert len({part.y_studs for part in deck}) == 4
