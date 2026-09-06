from brickhouse.scene import ArchitecturalScene, project_scene_to_building, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey

SOURCE = {"kind": "inferred", "confidence": 0.7}


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "survey-topology",
        "name": "Visible stair with hidden junction",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "front", "source": SOURCE},
            {"photo_index": 2, "facade": "left", "description": "left A", "source": SOURCE},
            {"photo_index": 3, "facade": "left", "description": "left B", "source": SOURCE},
        ],
        "observations": [
            {
                "id": "stair_visible", "kind": "stair", "facade": "left", "certainty": "certain",
                "statement": "lower exterior stair run is visible",
                "evidence": [{"photo_index": 2, "observation": "lower run is directly visible"}],
            },
            {
                "id": "concrete_landing", "kind": "platform", "facade": "left", "certainty": "certain",
                "statement": "concrete landing is visible beside the building",
                "evidence": [{"photo_index": 3, "observation": "landing surface is directly visible"}],
            },
        ],
        "relations": [{
            "id": "stair_to_landing",
            "kind": "connects_to",
            "subject_id": "stair_visible",
            "object_id": "concrete_landing",
            "certainty": "certain",
            "statement": "the stair belongs to the landing circulation, but the exact junction is occluded",
            "evidence": [
                {"photo_index": 2, "observation": "stair continues toward the occluded landing zone"},
                {"photo_index": 3, "observation": "landing appears in the same circulation zone"},
            ],
        }],
    })


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "scene-topology",
        "name": "Conservative visible geometry",
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
            "id": "concrete_landing",
            "host_volume_id": "main",
            "position": {"x": -2, "y": 3, "z": 1.4},
            "width": 2,
            "depth": 2,
            "thickness": 0.2,
            "material": "concrete",
            "source": SOURCE,
        }],
        "stairs": [{
            "id": "stair_visible",
            "start": {"x": -1, "y": 1, "z": 0},
            "end": {"x": -1, "y": 2.3, "z": 0.9},
            "width": 1,
            "material": "concrete",
            "source": SOURCE,
        }],
        "relations": [{
            "id": "stair_to_landing",
            "kind": "connects_to",
            "subject_id": "stair_visible",
            "object_id": "concrete_landing",
            "certainty": "certain",
            "geometry_status": "unresolved",
            "statement": "topological connection is certain; exact hidden junction is not metric yet",
            "evidence": [
                {"photo_index": 2, "observation": "stair heads toward landing"},
                {"photo_index": 3, "observation": "landing confirms circulation context"},
            ],
        }],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "white"},
        },
    })


def test_scene_preserves_certain_relation_without_inventing_hidden_metric_junction():
    scene = _scene()
    assert scene.relations[0].geometry_status == "unresolved"
    issues = validate_scene_against_survey(_survey(), scene)
    codes = {issue.code for issue in issues}
    assert "certain_relation_missing" not in codes
    assert "certain_connection_broken" not in codes
    assert "certain_connection_metric_unresolved" in codes


def test_unresolved_topology_blocks_lego_projection():
    projection = project_scene_to_building(_scene())
    assert projection.blocked
    assert projection.building is None
    assert "topological_relation_geometry_unresolved" in {issue.code for issue in projection.issues}


def test_scene_rejects_fully_floating_stair_even_with_unresolved_relation():
    payload = _scene().model_dump(mode="json")
    payload["stairs"][0]["start"] = {"x": -1, "y": 1, "z": 0.5}
    try:
        ArchitecturalScene.model_validate(payload)
    except ValueError as exc:
        assert "does not connect" in str(exc)
    else:
        raise AssertionError("a fully floating stair must remain invalid")


def test_resolved_scene_connection_passes_when_metric_contact_exists():
    payload = _scene().model_dump(mode="json")
    payload["stairs"][0]["end"] = {"x": -1, "y": 3, "z": 1.4}
    payload["relations"][0]["geometry_status"] = "resolved"

    scene = ArchitecturalScene.model_validate(payload)

    assert scene.relations[0].geometry_status == "resolved"


def test_resolved_scene_connection_rejects_metric_contradiction():
    payload = _scene().model_dump(mode="json")
    payload["relations"][0]["geometry_status"] = "resolved"

    try:
        ArchitecturalScene.model_validate(payload)
    except ValueError as exc:
        message = str(exc)
        assert "resolved scene relation 'stair_to_landing' connects_to" in message
        assert "not reflected by metric contact" in message
    else:
        raise AssertionError("a resolved connects_to claim must match concrete Scene geometry")


def test_unresolved_scene_connection_keeps_metric_gap_as_uncertainty():
    scene = _scene()

    assert scene.relations[0].geometry_status == "unresolved"
    assert scene.stairs[0].end.y < scene.platforms[0].position.y
