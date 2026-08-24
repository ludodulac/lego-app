from brickhouse.scene import ArchitecturalScene, SceneSurveySeverity, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


SOURCE = {"kind": "inferred", "confidence": 0.6}


def _survey(kind: str, object_id: str) -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "survey-partial-geometry",
        "name": "Partial exterior geometry",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "front", "source": SOURCE},
            {"photo_index": 2, "facade": "right", "description": "right", "source": SOURCE},
        ],
        "observations": [{
            "id": object_id,
            "kind": kind,
            "facade": "right",
            "certainty": "certain",
            "statement": f"{kind} exists but its hidden continuation is not established",
            "evidence": [{"photo_index": 2, "observation": "visible portion"}],
        }],
    })


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "scene-partial-geometry",
        "name": "Partial exterior geometry",
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
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "dark_brown"},
        },
        "notes": "Certain exterior element omitted because its hidden connection is not evidenced.",
    })


def test_certain_stair_may_be_omitted_instead_of_inventing_hidden_connection():
    issues = validate_scene_against_survey(_survey("stair", "stair_hidden"), _scene())
    matching = [issue for issue in issues if issue.object_id == "stair_hidden"]
    assert any(issue.code == "certain_stair_not_geometrically_encoded" for issue in matching)
    assert all(issue.severity is SceneSurveySeverity.WARNING for issue in matching)
    assert not any(issue.code == "certain_stair_missing" for issue in issues)


def test_certain_platform_may_be_omitted_instead_of_inventing_hidden_connection():
    issues = validate_scene_against_survey(_survey("platform", "deck_hidden"), _scene())
    matching = [issue for issue in issues if issue.object_id == "deck_hidden"]
    assert any(issue.code == "certain_platform_not_geometrically_encoded" for issue in matching)
    assert all(issue.severity is SceneSurveySeverity.WARNING for issue in matching)
    assert not any(issue.code == "certain_platform_missing" for issue in issues)
