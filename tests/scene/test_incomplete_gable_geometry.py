import pytest

from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene, project_scene_to_building

SOURCE = {"kind": "inferred", "confidence": 0.45}


def _scene(*, ridge_direction=None, pitch_degrees=None) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "gable-incomplete",
        "name": "Gable incomplete",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE},
            "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "roofs": [{
            "id": "roof",
            "volume_id": "main",
            "type": "gable",
            "overhang": 0.2,
            "ridge_direction": ridge_direction,
            "pitch_degrees": pitch_degrees,
            "source": SOURCE,
            "evidence": [{"photo_index": 1, "observation": "two pitched planes are visible"}],
        }],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}},
    })


def test_scene_can_preserve_certain_gable_shape_without_fake_pitch() -> None:
    scene = _scene(ridge_direction="depth", pitch_degrees=None)
    assert scene.roofs[0].type.value == "gable"
    assert scene.roofs[0].pitch_degrees is None


def test_incomplete_gable_blocks_projection_instead_of_creating_open_building() -> None:
    projection = project_scene_to_building(_scene(ridge_direction="depth", pitch_degrees=None))
    assert projection.building is None
    assert projection.blocked
    issue = next(issue for issue in projection.issues if issue.code == "gable_geometry_incomplete")
    assert issue.severity.value == "blocker"
    assert "open building" in issue.message


def test_gable_with_unknown_ridge_and_pitch_remains_scene_truth_without_fake_numbers() -> None:
    projection = project_scene_to_building(_scene())
    assert projection.building is None
    assert projection.blocked
    issue = next(issue for issue in projection.issues if issue.code == "gable_geometry_incomplete")
    assert "ridge_direction" in issue.message
    assert "pitch_degrees" in issue.message


def test_scene_pipeline_refuses_open_top_for_incomplete_gable() -> None:
    with pytest.raises(ValueError, match="open building"):
        run_m0_pipeline_scene(_scene(ridge_direction="depth", pitch_degrees=None), front_width_studs=48)
