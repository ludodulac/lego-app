from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_architecture import _scene_bounds
from brickhouse.bricks.scene_architecture_relations import (
    _platform_representation_shifts,
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


def _scene(*, stair_axis="x"):
    if stair_axis == "x":
        start = {"x": -1.3, "y": 2.5, "z": 0.0}
        end = {"x": -0.3, "y": 2.5, "z": 1.0}
    else:
        start = {"x": -0.3, "y": 1.0, "z": 0.0}
        end = {"x": -0.3, "y": 2.0, "z": 1.0}
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": f"shared-anchor-{stair_axis}",
            "name": "Generic shared platform stair anchor",
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
            "stairs": [
                {
                    "id": "run",
                    "start": start,
                    "end": end,
                    "width": 0.2,
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


def _shifts(scene):
    origin_x, origin_y, _ = _scene_bounds(scene)
    return _platform_representation_shifts(
        scene,
        origin_x=origin_x,
        origin_y=origin_y,
        studs_per_meter=5.0,
    )


def test_collinear_connected_stair_allows_platform_host_snap():
    scene = _scene(stair_axis="x")

    assert _shifts(scene)["landing"] == (1, 0)

    model = augment_brick_model_with_scene_architecture_relations(
        _base_model(), scene, front_width_studs=50
    )
    deck = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-platform:landing:deck:")
    ]
    treads = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-stair:run:tread:")
    ]
    shifted_wall = next(part for part in model.parts if part.placement_id == "wall")

    assert deck
    assert treads
    assert max(part.x_studs for part in deck) + 1 == shifted_wall.x_studs
    assert max(part.x_studs for part in treads) == max(part.x_studs for part in deck)
    assert len({part.y_studs for part in treads}) == 1


def test_perpendicular_endpoint_snap_is_rejected_instead_of_bending_stair():
    scene = _scene(stair_axis="y")

    assert _shifts(scene)["landing"] == (0, 0)

    model = augment_brick_model_with_scene_architecture_relations(
        _base_model(), scene, front_width_studs=50
    )
    deck = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-platform:landing:deck:")
    ]
    treads = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-stair:run:tread:")
    ]

    assert deck
    assert treads
    assert min(part.x_studs for part in deck) == 0
    assert {part.x_studs for part in treads} == {0}


def test_shared_anchor_keeps_source_scene_immutable_and_masonry_body_coherent():
    scene = _scene(stair_axis="x")
    source_before = scene.model_dump()

    model = augment_brick_model_with_scene_architecture_relations(
        _base_model(), scene, front_width_studs=50
    )
    treads = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-stair:run:tread:")
    ]
    body = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-stair:run:body:")
    ]
    supports = [
        part
        for part in model.parts
        if part.placement_id.startswith("scene-platform:landing:support1:")
    ]

    assert scene.model_dump() == source_before
    assert treads
    assert body
    assert supports
    terminal_x = max(part.x_studs for part in treads)
    terminal_z = max(part.z_plates for part in treads if part.x_studs == terminal_x)
    assert any(part.x_studs == terminal_x and part.z_plates < terminal_z for part in body)
    assert min(part.x_studs for part in supports) == terminal_x
    assert all(part.placement_id.startswith(("scene-stair:run:", "scene-platform:landing:")) for part in [*treads, *body, *supports])
