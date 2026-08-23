import pytest
from pydantic import ValidationError

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_architecture import augment_brick_model_with_scene_architecture
from brickhouse.building.models import Facade
from brickhouse.scene import ArchitecturalScene


def _source(confidence=.7):
    return {"kind": "inferred", "confidence": confidence}


def _scene(platform):
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "multi-volume-platform",
        "name": "Multi volume platform",
        "units": "m",
        "volumes": [
            {
                "id": "main",
                "position": {"x": 0, "y": 0, "z": 0},
                "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 1}},
                "depth": {"value": 8, "source": _source()},
                "height": {"value": 6, "source": _source()},
                "floors": 2,
                "source": _source(),
            },
            {
                "id": "annex",
                "position": {"x": 12, "y": 2, "z": 0},
                "width": {"value": 4, "source": _source()},
                "depth": {"value": 4, "source": _source()},
                "height": {"value": 3, "source": _source()},
                "floors": 1,
                "source": _source(),
            },
        ],
        "platforms": [platform],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "dark_brown"},
        },
    })


def _base_model():
    return BrickModel(
        building_id="multi-volume-platform",
        volume_id="composite",
        width_studs=80,
        depth_studs=40,
        height_plates=60,
        parts=[BrickModelPart(
            placement_id="seed",
            part_id="BRICK_1X1",
            category="brick",
            component="wall",
            x_studs=0,
            y_studs=0,
            z_plates=0,
            rotation_quarter_turns=0,
            facade=Facade.FRONT,
        )],
    )


def test_secondary_platform_is_validated_against_its_explicit_host_volume():
    platform = {
        "id": "annex_balcony",
        "host_volume_id": "annex",
        "position": {"x": 11, "y": 2.5, "z": 2},
        "width": 1,
        "depth": 2,
        "thickness": .2,
        "material": "timber",
        "deck_board_direction": "y",
        "edges": {
            "x_min": {"treatment": "open_railing"},
            "x_max": {"treatment": "wall_attached"},
            "y_min": {"treatment": "open_railing"},
            "y_max": {"treatment": "open_railing"},
        },
        "source": _source(),
    }
    scene = _scene(platform)
    model = augment_brick_model_with_scene_architecture(_base_model(), scene, front_width_studs=50)
    parts = [part for part in model.parts if part.placement_id.startswith("scene-platform:annex_balcony:")]
    assert parts
    assert all(part.facade is Facade.LEFT for part in parts)
    assert min(part.x_studs for part in parts) >= 55


def test_platform_host_volume_reference_must_exist():
    platform = {
        "id": "bad_platform",
        "host_volume_id": "missing",
        "position": {"x": -1, "y": 2, "z": 1},
        "width": 1,
        "depth": 2,
        "thickness": .2,
        "source": _source(),
    }
    with pytest.raises(ValidationError, match="unknown host volume"):
        _scene(platform)


def test_legacy_platform_without_host_volume_still_scopes_to_primary_volume():
    platform = {
        "id": "legacy_left_deck",
        "position": {"x": -1, "y": 2, "z": 1},
        "width": 1,
        "depth": 2,
        "thickness": .2,
        "material": "timber",
        "source": _source(),
    }
    scene = _scene(platform)
    model = augment_brick_model_with_scene_architecture(_base_model(), scene, front_width_studs=50)
    parts = [part for part in model.parts if part.placement_id.startswith("scene-platform:legacy_left_deck:")]
    assert parts
    assert all(part.facade is Facade.LEFT for part in parts)
