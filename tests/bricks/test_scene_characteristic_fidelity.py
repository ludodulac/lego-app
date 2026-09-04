from brickhouse.bricks.scene_characteristic_fidelity import (
    MATERIAL_CHARACTERISTIC_ERROR,
    SEVERE_CHARACTERISTIC_ERROR,
    characteristic_distortions,
    characteristic_fidelity_issues,
)
from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.9}


def _scene(*, platform_width=0.50, stair_width=0.50, chimney_width=0.30):
    prop = lambda value: {"value": value, "source": SOURCE, "evidence": []}
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "generic-characteristic-fidelity",
            "name": "Generic characteristic exterior fidelity",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "width": prop(8.0),
                    "depth": prop(6.0),
                    "height": prop(4.0),
                    "floors": 1,
                    "source": SOURCE,
                }
            ],
            "platforms": [
                {
                    "id": "deck",
                    "position": {"x": -platform_width, "y": 1.0, "z": 1.0},
                    "width": platform_width,
                    "depth": 2.0,
                    "thickness": 0.25,
                    "material": "timber",
                    "source": SOURCE,
                }
            ],
            "stairs": [
                {
                    "id": "stair",
                    "start": {"x": -1.5, "y": 2.0, "z": 0.0},
                    "end": {"x": -platform_width, "y": 2.0, "z": 1.0},
                    "width": stair_width,
                    "material": "timber",
                    "source": SOURCE,
                }
            ],
            "chimneys": [
                {
                    "id": "chimney",
                    "position": {"x": 2.0, "y": 2.0, "z": 3.0},
                    "width": chimney_width,
                    "depth": 0.55,
                    "height": 1.0,
                    "source": SOURCE,
                }
            ],
            "appearance": {},
        }
    )


def _relation_shift_scene():
    prop = lambda value: {"value": value, "source": SOURCE, "evidence": []}
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "generic-relation-shift-fidelity",
            "name": "Generic relation shift fidelity",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "width": prop(10.0),
                    "depth": prop(8.0),
                    "height": prop(6.0),
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
                    "source": SOURCE,
                }
            ],
            "stairs": [
                {
                    "id": "run",
                    "start": {"x": -1.3, "y": 2.5, "z": 0.0},
                    "end": {"x": -0.3, "y": 2.5, "z": 1.0},
                    "width": 0.2,
                    "material": "concrete",
                    "source": SOURCE,
                }
            ],
            "appearance": {},
        }
    )


def test_characteristic_metrics_mirror_renderer_quantization_without_mutating_scene():
    scene = _scene()
    before = scene.model_dump(mode="json", by_alias=True)

    metrics = characteristic_distortions(scene, front_width_studs=32)
    by_id = {metric.object_id: metric for metric in metrics}

    assert by_id["deck"].worst_relative_error == 0.0
    assert by_id["stair"].worst_relative_error < MATERIAL_CHARACTERISTIC_ERROR
    assert 0 < by_id["chimney"].worst_relative_error < MATERIAL_CHARACTERISTIC_ERROR
    assert by_id["chimney"].position_error_fraction >= 0
    assert scene.model_dump(mode="json", by_alias=True) == before


def test_severe_platform_extent_quantization_is_a_blocker():
    scene = _scene(platform_width=0.26)

    issues = characteristic_fidelity_issues(scene, front_width_studs=32)
    platform = next(issue for issue in issues if issue.object_id == "deck")

    assert platform.code == "lego_platform_proportion_distortion"
    assert platform.severity == "blocker"
    assert "1.040->2 studs" in platform.message


def test_severe_stair_width_quantization_is_a_blocker():
    scene = _scene(stair_width=0.10)

    metrics = characteristic_distortions(scene, front_width_studs=32)
    stair = next(metric for metric in metrics if metric.object_id == "stair")
    issues = characteristic_fidelity_issues(scene, front_width_studs=32)
    stair_issue = next(issue for issue in issues if issue.object_id == "stair")

    assert stair.worst_relative_error >= SEVERE_CHARACTERISTIC_ERROR
    assert stair_issue.code == "lego_stair_proportion_distortion"
    assert stair_issue.severity == "blocker"


def test_relation_snap_distortion_uses_final_adjusted_stair_run():
    scene = _relation_shift_scene()

    metrics = characteristic_distortions(scene, front_width_studs=50)
    stair = next(metric for metric in metrics if metric.object_id == "run")
    issues = characteristic_fidelity_issues(scene, front_width_studs=50)
    stair_issue = next(issue for issue in issues if issue.object_id == "run")

    assert "run 5.000->6 studs" in stair.details
    assert stair.worst_relative_error >= MATERIAL_CHARACTERISTIC_ERROR
    assert stair_issue.severity == "warning"


def test_scene_pipeline_surfaces_characteristic_distortion_diagnostics():
    scene = _scene(platform_width=0.26)
    before = scene.model_dump(mode="json", by_alias=True)

    bundle = run_m0_pipeline_scene(scene, front_width_studs=32)

    issue = next(
        item
        for item in bundle.fidelity_issues
        if item.code == "lego_platform_proportion_distortion"
    )
    assert issue.object_id == "deck"
    assert issue.severity == "blocker"
    assert scene.model_dump(mode="json", by_alias=True) == before
