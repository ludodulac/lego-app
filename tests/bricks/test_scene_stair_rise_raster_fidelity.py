from brickhouse.bricks.scene_stair_connectivity_fidelity import stair_connectivity_fidelity_issues
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.8}


def _scene(*, end_z: float, platform_z: float) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "stair-rise-fidelity",
            "name": "Generic stair rise fidelity",
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
                    "position": {"x": -0.3, "y": 1.8, "z": platform_z},
                    "width": 0.2,
                    "depth": 0.4,
                    "thickness": 0.1,
                    "material": "concrete",
                    "source": SOURCE,
                }
            ],
            "stairs": [
                {
                    "id": "run",
                    "start": {"x": -1.5, "y": 2.0, "z": 0.0},
                    "end": {"x": -0.25, "y": 2.0, "z": end_z},
                    "width": 0.01,
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


def _rise_issues(scene):
    return [
        issue
        for issue in stair_connectivity_fidelity_issues(scene, front_width_studs=50)
        if issue.code == "lego_stair_vertical_rise_collapsed"
    ]


def test_nonzero_metric_rise_collapsed_to_same_course_is_reported():
    scene = _scene(end_z=0.11, platform_z=0.11)

    issues = _rise_issues(scene)

    assert len(issues) == 1
    assert issues[0].severity == "blocker"
    assert issues[0].object_id == "run"
    assert "0.11m vertical rise" in issues[0].message
    assert "course Z=0 plates" in issues[0].message
    assert "no artificial extra brick course" in issues[0].message


def test_rise_that_quantizes_to_distinct_course_is_not_reported():
    scene = _scene(end_z=0.13, platform_z=0.13)

    assert _rise_issues(scene) == []


def test_bh108_shared_platform_course_can_preserve_rise_without_warning():
    # The endpoint itself would quantize to course 0 at 5 studs/m, but it is
    # Scene-connected to a 0.13m platform. BH-108 makes the stair share the
    # platform course (3 plates), so the final representation keeps vertical rise.
    scene = _scene(end_z=0.11, platform_z=0.13)

    assert _rise_issues(scene) == []


def test_stair_rise_fidelity_audit_keeps_source_scene_immutable():
    scene = _scene(end_z=0.11, platform_z=0.11)
    before = scene.model_dump()

    _rise_issues(scene)

    assert scene.model_dump() == before
