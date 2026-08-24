from brickhouse.scene import ArchitecturalScene, ProjectionSeverity, project_scene_to_building

SOURCE = {"kind": "inferred", "confidence": 0.35}
USER = {"kind": "user_provided", "confidence": 1.0}


def _scene(*, width=10.0, depth=None, height=None) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "partial-envelope",
        "name": "Partial envelope",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": width, "source": USER if width is not None else SOURCE},
            "depth": {"value": depth, "source": SOURCE},
            "height": {"value": height, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "openings": [{
            "id": "front_window",
            "type": "window",
            "volume_id": "main",
            "facade": "front",
            "offset_horizontal": 2.0,
            "offset_vertical": 2.0,
            "width": 1.0,
            "height": 1.2,
            "source": SOURCE,
        }],
        "appearance": {"walls": {"color": "off_white"}},
        "notes": "Front width is known; depth and overall height are not sufficiently constrained.",
    })


def test_scene_can_preserve_unknown_depth_and_height_as_null() -> None:
    scene = _scene()
    assert scene.volumes[0].width.value == 10.0
    assert scene.volumes[0].depth.value is None
    assert scene.volumes[0].height.value is None
    assert scene.openings[0].id == "front_window"


def test_unknown_volume_metric_blocks_projection_instead_of_becoming_a_guess() -> None:
    projection = project_scene_to_building(_scene())
    assert projection.building is None
    issue = next(issue for issue in projection.issues if issue.code == "volume_geometry_incomplete")
    assert issue.severity is ProjectionSeverity.BLOCKER
    assert "depth" in issue.message
    assert "height" in issue.message


def test_complete_envelope_still_projects_normally() -> None:
    projection = project_scene_to_building(_scene(depth=8.0, height=6.0))
    assert projection.building is not None
    assert not any(issue.code == "volume_geometry_incomplete" for issue in projection.issues)
    assert projection.building.volumes[0].depth == 8.0
