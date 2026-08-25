import pytest

from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene, project_scene_to_building

SOURCE = {"kind": "inferred", "confidence": 0.6}


def _scene(*, down_slope_direction="rear", pitch_degrees=None) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "shed-incomplete",
        "name": "Shed incomplete",
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
            "id": "roof_main",
            "volume_id": "main",
            "type": "shed",
            "overhang": 0.2,
            "ridge_direction": None,
            "down_slope_direction": down_slope_direction,
            "pitch_degrees": pitch_degrees,
            "source": SOURCE,
            "evidence": [{
                "photo_index": 2,
                "observation": "The roof edge visibly falls from front toward rear.",
            }],
        }],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
        },
    })


def test_scene_preserves_known_shed_direction_without_fake_pitch() -> None:
    scene = _scene()
    roof = scene.roofs[0]
    assert roof.type.value == "shed"
    assert roof.down_slope_direction.value == "rear"
    assert roof.pitch_degrees is None


def test_known_direction_unknown_pitch_blocks_only_on_pitch() -> None:
    projection = project_scene_to_building(_scene())
    assert projection.building is None
    assert projection.blocked
    blockers = [issue for issue in projection.issues if issue.severity.value == "blocker"]
    assert len(blockers) == 1
    issue = blockers[0]
    assert issue.code == "shed_geometry_incomplete"
    assert issue.object_id == "roof_main"
    assert "pitch_degrees" in issue.message
    assert "down_slope_direction" not in issue.message.split("does not know", 1)[1].split(".", 1)[0]
    assert "false gable/flat roof" in issue.message


def test_missing_direction_and_pitch_reports_both_without_invention() -> None:
    projection = project_scene_to_building(_scene(down_slope_direction=None))
    issue = next(issue for issue in projection.issues if issue.code == "shed_geometry_incomplete")
    missing = issue.message.split("does not know", 1)[1].split(".", 1)[0]
    assert "down_slope_direction" in missing
    assert "pitch_degrees" in missing


def test_scene_pipeline_refuses_to_quantize_unknown_shed_pitch() -> None:
    with pytest.raises(ValueError, match="pitch_degrees"):
        run_m0_pipeline_scene(_scene(), front_width_studs=48)
