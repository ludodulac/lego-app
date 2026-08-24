from brickhouse.scene import ArchitecturalScene, project_scene_to_building, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey

SOURCE = {"kind": "inferred", "confidence": 0.55}
USER_SOURCE = {"kind": "user_provided", "confidence": 0.99}


def _survey(*, gable_certainty: str = "plausible") -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "roof-fidelity-survey",
        "name": "Roof fidelity survey",
        "photos": [
            {
                "photo_index": 1,
                "facade": "front",
                "description": "front view with visible roof silhouette",
                "source": USER_SOURCE,
            }
        ],
        "observations": [
            {
                "id": "roof_observed",
                "kind": "roof",
                "facade": "front",
                "certainty": "certain",
                "statement": "A roof is certainly visible above the facade",
                "evidence": [
                    {"photo_index": 1, "observation": "roof silhouette clearly visible"}
                ],
                "attributes": {"facade_is_gable": True},
                "attribute_certainty": {"facade_is_gable": gable_certainty},
            }
        ],
    })


def _scene(*, roofs) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "roof-fidelity-scene",
        "name": "Roof fidelity scene",
        "units": "m",
        "volumes": [
            {
                "id": "main",
                "position": {"x": 0, "y": 0, "z": 0},
                "width": {"value": 9, "source": SOURCE},
                "depth": {"value": 7, "source": SOURCE},
                "height": {"value": 5, "source": SOURCE},
                "floors": 2,
                "source": SOURCE,
            }
        ],
        "roofs": roofs,
        "appearance": {"walls": {"color": "white"}, "roof": {"color": "gray"}},
    })


def test_certain_roof_existence_cannot_disappear_when_shape_is_only_plausible() -> None:
    issues = validate_scene_against_survey(_survey(), _scene(roofs=[]))
    codes = {issue.code for issue in issues}
    assert "certain_roof_missing" in codes
    assert "certain_gable_lost" not in codes


def test_preserving_unknown_roof_shape_satisfies_existence_invariant() -> None:
    scene = _scene(roofs=[{
        "id": "roof_scene",
        "volume_id": "main",
        "type": "other",
        "overhang": 0,
        "ridge_direction": None,
        "pitch_degrees": None,
        "source": SOURCE,
        "evidence": [{"photo_index": 1, "observation": "roof exists; exact shape uncertain"}],
    }])
    issues = validate_scene_against_survey(_survey(), scene)
    assert "certain_roof_missing" not in {issue.code for issue in issues}


def test_scene_roof_that_engine_cannot_render_blocks_open_building() -> None:
    scene = _scene(roofs=[{
        "id": "roof_scene",
        "volume_id": "main",
        "type": "other",
        "overhang": 0,
        "ridge_direction": None,
        "pitch_degrees": None,
        "source": SOURCE,
    }])
    projection = project_scene_to_building(scene)
    assert projection.building is None
    assert projection.blocked
    issue = next(issue for issue in projection.issues if issue.code == "roof_type_not_supported")
    assert issue.severity.value == "blocker"
