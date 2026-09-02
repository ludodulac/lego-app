import pytest

from brickhouse.bricks.scene_supports import (
    platform_support_level_mismatches,
    validate_platform_support_footprints,
)
from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene

SOURCE = {"kind": "inferred", "confidence": 0.8}


def _scene(*, support_position=None, support_height=1.0):
    support_position = support_position or {"x": 10.2, "y": 2.3, "z": 0.0}
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "generic-support-audit",
        "name": "Generic support audit",
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
        "platforms": [{
            "id": "deck",
            "position": {"x": 10, "y": 2, "z": 1},
            "width": 2,
            "depth": 4,
            "thickness": 0.2,
            "material": "timber",
            "supports": [{
                "id": "post-a",
                "position": support_position,
                "width": 0.2,
                "depth": 0.2,
                "height": support_height,
                "source": SOURCE,
            }],
            "source": SOURCE,
        }],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "dark_brown"},
        },
    })


def test_declared_support_inside_platform_footprint_is_valid():
    validate_platform_support_footprints(_scene())


def test_declared_support_outside_platform_footprint_is_rejected():
    scene = _scene(support_position={"x": 12.5, "y": 2.3, "z": 0.0})
    with pytest.raises(ValueError, match="support 'post-a' lies outside"):
        validate_platform_support_footprints(scene)


def test_matching_support_top_has_no_level_fidelity_mismatch():
    assert platform_support_level_mismatches(_scene()) == []


def test_support_level_mismatch_is_reported_without_mutating_scene():
    scene = _scene(support_height=0.5)
    before = scene.model_dump()
    mismatches = platform_support_level_mismatches(scene)
    assert len(mismatches) == 1
    assert mismatches[0].platform_id == "deck"
    assert mismatches[0].support_id == "post-a"
    assert mismatches[0].delta_m == pytest.approx(0.5)
    assert scene.model_dump() == before


def test_scene_pipeline_blocks_outside_metric_support_before_rendering():
    scene = _scene(support_position={"x": 12.5, "y": 2.3, "z": 0.0})
    with pytest.raises(ValueError, match="declared SupportPost geometry"):
        run_m0_pipeline_scene(scene, front_width_studs=40)


def test_scene_pipeline_surfaces_vertical_support_mismatch_as_fidelity_issue():
    scene = _scene(support_height=0.5)
    before = scene.model_dump()
    bundle = run_m0_pipeline_scene(scene, front_width_studs=40)
    issues = [
        issue for issue in bundle.fidelity_issues
        if issue.code == "platform_support_level_mismatch"
    ]
    assert len(issues) == 1
    assert issues[0].object_id == "post-a"
    assert issues[0].severity == "warning"
    assert scene.model_dump() == before
