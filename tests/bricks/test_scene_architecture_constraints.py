from __future__ import annotations

import pytest

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_architecture import augment_brick_model_with_scene_architecture
from brickhouse.scene.models import ArchitecturalScene


def _base_model() -> BrickModel:
    return BrickModel(
        building_id="house",
        volume_id="volume_main",
        width_studs=48,
        depth_studs=40,
        height_plates=60,
        parts=[BrickModelPart(
            placement_id="wall-1",
            part_id="BRICK_1X1",
            category="brick",
            component="wall",
            x_studs=0,
            y_studs=0,
            z_plates=0,
            rotation_quarter_turns=0,
            facade="front",
        )],
    )


def _scene(*, platforms=None, stairs=None) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "scene",
        "name": "scene",
        "units": "m",
        "volumes": [{
            "id": "volume_main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 1}},
            "depth": {"value": 8, "source": {"kind": "inferred", "confidence": .5}},
            "height": {"value": 7, "source": {"kind": "inferred", "confidence": .5}},
            "floors": 2,
            "source": {"kind": "inferred", "confidence": .5},
        }],
        "platforms": platforms or [],
        "stairs": stairs or [],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
    })


def test_turning_stair_must_be_split_into_runs() -> None:
    scene = _scene(stairs=[{
        "id": "stair",
        "start": {"x": -1, "y": 2, "z": 0},
        "end": {"x": -2, "y": 4, "z": 2},
        "width": 1,
        "source": {"kind": "inferred", "confidence": .5},
    }])
    with pytest.raises(ValueError, match="split turning stairs"):
        augment_brick_model_with_scene_architecture(_base_model(), scene, front_width_studs=48)


def test_platform_wrapping_corner_must_be_split() -> None:
    scene = _scene(platforms=[{
        "id": "corner_deck",
        "position": {"x": -2, "y": -2, "z": 2},
        "width": 2,
        "depth": 2,
        "thickness": .2,
        "supports": [],
        "source": {"kind": "inferred", "confidence": .5},
    }])
    with pytest.raises(ValueError, match="wraps a building corner"):
        augment_brick_model_with_scene_architecture(_base_model(), scene, front_width_studs=48)


def test_timber_platform_does_not_invent_supports() -> None:
    scene = _scene(platforms=[{
        "id": "timber_deck",
        "position": {"x": -2, "y": 2, "z": 2},
        "width": 2,
        "depth": 3,
        "thickness": .2,
        "supports": [],
        "source": {"kind": "inferred", "confidence": .5},
        "evidence": [{"photo_index": 1, "observation": "timber wood deck"}],
    }])
    out = augment_brick_model_with_scene_architecture(_base_model(), scene, front_width_studs=48)
    assert not any(":support" in part.placement_id for part in out.parts)
