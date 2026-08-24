from brickhouse.scene import ArchitecturalScene, project_scene_to_building

SOURCE = {"kind": "inferred", "confidence": 0.6}


def test_unresolved_platform_relation_may_reference_survey_boundary_anchor():
    scene = ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "scene-boundary-anchor",
        "name": "Boundary anchor",
        "units": "m",
        "volumes": [{
            "id": "volume_main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE},
            "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "platforms": [{
            "id": "terrace_anchor",
            "position": {"x": 12, "y": 3, "z": 1.2},
            "width": 2,
            "depth": 2,
            "thickness": 0.2,
            "supports": [],
            "source": SOURCE,
        }],
        "relations": [{
            "id": "terrace_to_building_boundary",
            "kind": "connects_to",
            "subject_id": "terrace_anchor",
            "object_id": "building_boundary_front",
            "certainty": "certain",
            "geometry_status": "unresolved",
            "statement": "The terrace is attached to the building envelope but the metric junction is occluded.",
            "evidence": [{"photo_index": 2, "observation": "terrace reaches the house"}],
        }],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "white"},
        },
    })

    assert scene.relations[0].object_id == "building_boundary_front"
    projection = project_scene_to_building(scene)
    assert projection.blocked
    assert any(issue.code == "topological_relation_geometry_unresolved" for issue in projection.issues)


def test_resolved_relation_still_requires_two_scene_objects():
    payload = {
        "schema_version": "0.2",
        "id": "scene-bad-resolved",
        "name": "Bad resolved anchor",
        "units": "m",
        "volumes": [{
            "id": "volume_main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE},
            "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "relations": [{
            "id": "bad",
            "kind": "connects_to",
            "subject_id": "volume_main",
            "object_id": "missing_anchor",
            "certainty": "certain",
            "geometry_status": "resolved",
            "statement": "bad",
            "evidence": [],
        }],
        "appearance": {"walls": None, "roof": None, "frames": None},
    }

    try:
        ArchitecturalScene.model_validate(payload)
    except ValueError as exc:
        assert "resolved scene relation" in str(exc)
    else:
        raise AssertionError("resolved relation to a missing Scene object must fail")
