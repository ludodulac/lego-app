from brickhouse.scene import ArchitecturalScene, SceneRoofType, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


SOURCE = {"kind": "inferred", "confidence": 0.6}


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
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "generic-roof-fidelity",
            "name": "Generic roof fidelity",
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
                }
            ],
            "roofs": [
                {
                    "id": "roof",
                    "volume_id": "main",
                    "type": "gable",
                    "overhang": 0.2,
                    "ridge_direction": None,
                    "pitch_degrees": None,
                    "source": SOURCE,
                    "evidence": [{"photo_index": 1, "observation": "gable hypothesis visible"}],
                }
            ],
            "appearance": {},
        }
    )


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
    assert scene.roofs[0].ridge_direction is None
    assert scene.roofs[0].pitch_degrees is None
    assert "survey_gable_hypothesis_lost" not in _codes(_survey_with_facade_gable(), scene)


def test_unproven_facade_gable_does_not_force_gable_scene() -> None:
    scene = _scene()
    roof = scene.roofs[0].model_copy(update={"type": SceneRoofType.OTHER})
    degraded = scene.model_copy(update={"roofs": [roof]})

    assert "survey_gable_hypothesis_lost" not in _codes(
        _survey_with_facade_gable("unproven"), degraded
    )
