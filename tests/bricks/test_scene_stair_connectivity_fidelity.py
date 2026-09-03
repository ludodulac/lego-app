from brickhouse.bricks.scene_stair_connectivity_fidelity import stair_connectivity_fidelity_issues
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.8}


def _volume_scene(*, unsafe_perpendicular=False):
    if unsafe_perpendicular:
        start = {"x": -1.0, "y": -0.1, "z": 0.0}
        end = {"x": 0.5, "y": -0.1, "z": 1.0}
    else:
        start = {"x": -1.1, "y": 2.0, "z": 0.0}
        end = {"x": -0.1, "y": 2.0, "z": 1.0}
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "stair-volume-fidelity",
            "name": "Generic direct stair boundary fidelity",
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
                    "start": start,
                    "end": end,
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


def _platform_scene(*, endpoint_x):
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "stair-platform-fidelity",
            "name": "Generic stair platform fidelity",
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
                    "position": {"x": -2.0, "y": 2.0, "z": 1.0},
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
                    "start": {"x": -2.7, "y": 2.5, "z": 0.0},
                    "end": {"x": endpoint_x, "y": 2.5, "z": 1.0},
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


def test_safe_direct_volume_anchor_emits_no_connectivity_warning():
    scene = _volume_scene()
    source_before = scene.model_dump()

    issues = stair_connectivity_fidelity_issues(scene, front_width_studs=50)

    assert not any(issue.code.startswith("lego_stair_") for issue in issues)
    assert scene.model_dump() == source_before


def test_unsafe_perpendicular_volume_anchor_reports_real_final_contact_loss():
    scene = _volume_scene(unsafe_perpendicular=True)

    issues = stair_connectivity_fidelity_issues(scene, front_width_studs=50)
    losses = [issue for issue in issues if issue.code == "lego_stair_volume_contact_not_preserved"]

    assert len(losses) == 1
    assert losses[0].object_id == "run"
    assert "end" in losses[0].message
    assert "main" in losses[0].message
    assert "front" in losses[0].message


def test_platform_tolerance_contact_lost_by_raster_is_reported():
    scene = _platform_scene(endpoint_x=-1.7)

    issues = stair_connectivity_fidelity_issues(scene, front_width_studs=50)
    losses = [issue for issue in issues if issue.code == "lego_stair_platform_contact_not_preserved"]

    assert len(losses) == 1
    assert losses[0].object_id == "run"
    assert "end" in losses[0].message
    assert "landing" in losses[0].message


def test_platform_contact_that_survives_raster_emits_no_warning():
    scene = _platform_scene(endpoint_x=-1.9)

    issues = stair_connectivity_fidelity_issues(scene, front_width_studs=50)

    assert not any(issue.code == "lego_stair_platform_contact_not_preserved" for issue in issues)


def test_ground_endpoint_near_volume_is_not_reinterpreted_as_volume_loss():
    scene = ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "ground-priority-fidelity",
            "name": "Ground priority fidelity",
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
                    "start": {"x": -0.1, "y": 2.0, "z": 0.0},
                    "end": {"x": 0.0, "y": 2.0, "z": 1.0},
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

    issues = stair_connectivity_fidelity_issues(scene, front_width_studs=50)

    assert not any(
        issue.code == "lego_stair_volume_contact_not_preserved" and "start" in issue.message
        for issue in issues
    )
