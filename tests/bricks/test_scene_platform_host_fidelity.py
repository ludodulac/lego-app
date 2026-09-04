from brickhouse.bricks.scene_platform_connectivity import platform_connectivity_fidelity_issues
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.8}


def _scene(*, stair_axis: str | None = None):
    stairs = []
    if stair_axis == "x":
        stairs.append(
            {
                "id": "run",
                "start": {"x": -1.3, "y": 2.5, "z": 0.0},
                "end": {"x": -0.3, "y": 2.5, "z": 1.0},
                "width": 0.01,
                "material": "concrete",
                "source": SOURCE,
            }
        )
    elif stair_axis == "y":
        stairs.append(
            {
                "id": "run",
                "start": {"x": -0.3, "y": 1.0, "z": 0.0},
                "end": {"x": -0.3, "y": 2.0, "z": 1.0},
                "width": 0.01,
                "material": "concrete",
                "source": SOURCE,
            }
        )
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "platform-host-fidelity",
            "name": "Generic platform host fidelity",
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
                    "source": SOURCE,
                }
            ],
            "stairs": stairs,
            "appearance": {
                "walls": {"color": "off_white"},
                "roof": {"color": "dark_gray"},
                "frames": {"color": "dark_brown"},
            },
        }
    )


def _host_issues(scene):
    return [
        issue
        for issue in platform_connectivity_fidelity_issues(scene, front_width_studs=50)
        if issue.code == "lego_platform_host_contact_not_preserved"
    ]


def test_safe_platform_host_snap_has_no_fidelity_issue():
    scene = _scene()

    assert _host_issues(scene) == []


def test_collinear_stair_coordinated_host_snap_has_no_fidelity_issue():
    scene = _scene(stair_axis="x")

    assert _host_issues(scene) == []


def test_perpendicular_stair_refusal_surfaces_lost_host_contact():
    scene = _scene(stair_axis="y")

    issues = _host_issues(scene)

    assert len(issues) == 1
    assert issues[0].object_id == "landing"
    assert "host volume 'main'" in issues[0].message
    assert "left facade" in issues[0].message
    assert "stronger stair relation" in issues[0].message


def test_platform_host_fidelity_audit_keeps_source_scene_immutable():
    scene = _scene(stair_axis="y")
    before = scene.model_dump()

    _host_issues(scene)

    assert scene.model_dump() == before
