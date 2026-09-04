from brickhouse.bricks.scene_stair_connectivity_fidelity import stair_connectivity_fidelity_issues
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.8}


def _platform_scene(*, end_x: float = 2.08) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "short-stair-run",
            "name": "Generic short stair run",
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
                    "position": {"x": 2.0, "y": -0.3, "z": 1.0},
                    "width": 0.5,
                    "depth": 0.2,
                    "thickness": 0.2,
                    "material": "concrete",
                    "source": SOURCE,
                }
            ],
            "stairs": [
                {
                    "id": "run",
                    "start": {"x": 2.0, "y": -0.1, "z": 0.0},
                    "end": {"x": end_x, "y": -0.1, "z": 1.0},
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


def _direct_boundary_scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "short-stair-run-rescued",
            "name": "Generic short stair run rescued by boundary anchor",
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
            "stairs": [
                {
                    "id": "run",
                    "start": {"x": -0.16, "y": 2.0, "z": 0.0},
                    "end": {"x": -0.08, "y": 2.0, "z": 1.0},
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


def _collapse_issues(scene):
    return [
        issue
        for issue in stair_connectivity_fidelity_issues(scene, front_width_studs=50)
        if issue.code == "lego_stair_horizontal_run_collapsed"
    ]


def test_short_metric_run_collapsed_to_one_stud_coordinate_is_reported():
    scene = _platform_scene(end_x=2.08)

    issues = _collapse_issues(scene)

    assert len(issues) == 1
    assert issues[0].object_id == "run"
    assert "0.08m horizontal X run" in issues[0].message
    assert "both quantize to X=10" in issues[0].message
    assert "no artificial extra stud" in issues[0].message


def test_run_with_distinct_final_stud_coordinates_is_not_reported():
    scene = _platform_scene(end_x=2.3)

    assert _collapse_issues(scene) == []


def test_relation_aware_volume_anchor_that_rescues_short_run_is_not_reported():
    scene = _direct_boundary_scene()

    assert _collapse_issues(scene) == []


def test_stair_run_fidelity_audit_keeps_source_scene_immutable():
    scene = _platform_scene(end_x=2.08)
    before = scene.model_dump()

    _collapse_issues(scene)

    assert scene.model_dump() == before
