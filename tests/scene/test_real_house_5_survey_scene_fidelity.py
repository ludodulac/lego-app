from brickhouse.scene import ArchitecturalScene, SceneSurveySeverity, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


SOURCE = {"kind": "observed", "confidence": 0.9}


def test_scene_preserves_certain_survey_relation_without_benchmark_geometry() -> None:
    survey = ArchitecturalSurvey.model_validate(
        {
            "schema_version": "0.1",
            "id": "generic-fidelity-survey",
            "name": "Generic fidelity survey",
            "photos": [
                {
                    "photo_index": 1,
                    "facade": "front",
                    "description": "canonical front",
                    "source": SOURCE,
                },
                {
                    "photo_index": 2,
                    "facade": "left",
                    "description": "connection view",
                    "source": SOURCE,
                },
            ],
            "observations": [
                {
                    "id": "annex",
                    "kind": "volume",
                    "facade": "left",
                    "certainty": "certain",
                    "statement": "annex exists",
                    "evidence": [{"photo_index": 2, "observation": "annex visible"}],
                },
                {
                    "id": "main-boundary",
                    "kind": "building_boundary",
                    "facade": "left",
                    "certainty": "certain",
                    "statement": "main boundary visible",
                    "evidence": [{"photo_index": 2, "observation": "boundary visible"}],
                },
            ],
            "relations": [
                {
                    "id": "annex-connects-main",
                    "kind": "connects_to",
                    "subject_id": "annex",
                    "object_id": "main-boundary",
                    "certainty": "certain",
                    "statement": "annex connects to main boundary",
                    "evidence": [{"photo_index": 2, "observation": "contact visible"}],
                }
            ],
        }
    )
    scene = ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "generic-fidelity-scene",
            "name": "Generic fidelity scene",
            "units": "m",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "width": {"value": 10, "source": SOURCE},
                    "depth": {"value": 8, "source": SOURCE},
                    "height": {"value": 6, "source": SOURCE},
                    "floors": 2,
                    "source": SOURCE,
                },
                {
                    "id": "annex",
                    "position": {"x": -2, "y": 2, "z": 0},
                    "width": {"value": 2, "source": SOURCE},
                    "depth": {"value": 2, "source": SOURCE},
                    "height": {"value": 2, "source": SOURCE},
                    "floors": 1,
                    "source": SOURCE,
                },
            ],
            "relations": [
                {
                    "id": "annex-connects-main",
                    "kind": "connects_to",
                    "subject_id": "annex",
                    "object_id": "main-boundary",
                    "certainty": "certain",
                    "geometry_status": "resolved",
                    "semantic_anchor_volume_id": "main",
                    "statement": "annex connects to main boundary",
                    "evidence": [{"photo_index": 2, "observation": "contact visible"}],
                }
            ],
            "appearance": {},
        }
    )

    issues = validate_scene_against_survey(survey, scene)
    errors = [issue for issue in issues if issue.severity is SceneSurveySeverity.ERROR]
    assert errors == [], [(issue.code, issue.object_id, issue.message) for issue in errors]
    assert [relation.id for relation in scene.relations] == ["annex-connects-main"]
