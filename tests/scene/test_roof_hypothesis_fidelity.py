import json
from pathlib import Path

from brickhouse.scene import ArchitecturalScene, SceneRoofType, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


FIXTURE = Path(__file__).parents[1] / "fixtures" / "architectural_scene_real_house_5_v02.json"


def _survey_with_facade_gable(certainty: str = "plausible") -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(
        {
            "schema_version": "0.1",
            "id": "roof-fidelity",
            "name": "Roof fidelity",
            "photos": [
                {
                    "photo_index": 1,
                    "facade": "front",
                    "description": "Front gable view",
                    "source": {"kind": "user_provided", "confidence": 0.99},
                    "image_left_maps_to_facade_offset": "low",
                },
                {
                    "photo_index": 2,
                    "facade": "right",
                    "description": "Side roof view",
                    "source": {"kind": "user_provided", "confidence": 0.99},
                    "image_left_maps_to_facade_offset": "low",
                },
            ],
            "observations": [
                {
                    "id": "roof-observation",
                    "kind": "roof",
                    "facade": "front",
                    "certainty": "certain",
                    "statement": "Roof exists and the front facade is plausibly a gable end.",
                    "evidence": [
                        {"photo_index": 1, "observation": "Triangular roof/facade relationship visible."},
                        {"photo_index": 2, "observation": "Sloped roof continuity visible from the side."},
                    ],
                    "attributes": {"facade_is_gable": True},
                    "attribute_certainty": {"facade_is_gable": certainty},
                }
            ],
        }
    )


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _codes(survey: ArchitecturalSurvey, scene: ArchitecturalScene) -> set[str]:
    return {issue.code for issue in validate_scene_against_survey(survey, scene)}


def test_plausible_facade_gable_cannot_silently_degrade_to_other() -> None:
    scene = _scene()
    roof = scene.roofs[0].model_copy(update={"type": SceneRoofType.OTHER})
    degraded = scene.model_copy(update={"roofs": [roof]})

    assert "survey_gable_hypothesis_lost" in _codes(_survey_with_facade_gable(), degraded)


def test_plausible_facade_gable_is_preserved_by_gable_scene_without_forcing_metrics() -> None:
    scene = _scene()

    assert scene.roofs[0].type is SceneRoofType.GABLE
    assert "survey_gable_hypothesis_lost" not in _codes(_survey_with_facade_gable(), scene)


def test_unproven_facade_gable_does_not_force_gable_scene() -> None:
    scene = _scene()
    roof = scene.roofs[0].model_copy(update={"type": SceneRoofType.OTHER})
    degraded = scene.model_copy(update={"roofs": [roof]})

    assert "survey_gable_hypothesis_lost" not in _codes(
        _survey_with_facade_gable("unproven"), degraded
    )
