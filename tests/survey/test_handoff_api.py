from copy import deepcopy

import pytest

from brickhouse.survey.handoff_api import (
    HumanFactSceneHandoffRequest,
    prepare_human_fact_scene_handoff,
)
from brickhouse.survey.models import ArchitecturalSurvey


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(
        {
            "schema_version": "0.1",
            "id": "generic-access-house",
            "name": "Generic access house",
            "photos": [
                {
                    "photo_index": 1,
                    "facade": "front",
                    "description": "Canonical front view.",
                    "source": {"kind": "observed", "confidence": 1.0},
                    "image_left_maps_to_facade_offset": "low",
                },
                {
                    "photo_index": 2,
                    "facade": "left",
                    "description": "Exterior stair is visible.",
                    "source": {"kind": "observed", "confidence": 1.0},
                    "image_left_maps_to_facade_offset": "low",
                },
            ],
            "known_measurements": [],
            "observations": [
                {
                    "id": "access-stair",
                    "kind": "stair",
                    "facade": "left",
                    "certainty": "certain",
                    "statement": "Exterior stair exists.",
                    "evidence": [
                        {"photo_index": 2, "observation": "Exterior stair is visible."}
                    ],
                }
            ],
        }
    )


def _request(**fact_updates) -> HumanFactSceneHandoffRequest:
    fact = {
        "observation_id": "access-stair",
        "attribute_name": "stair_topology",
        "value": {
            "minimum_run_count": 2,
            "direction_change": True,
            "turning_node_kind": "turn_or_landing",
        },
        "certainty": "certain",
        "source": {"kind": "user_provided", "confidence": 1.0},
        "statement": "User confirms that the stair changes direction.",
    }
    fact.update(fact_updates)
    return HumanFactSceneHandoffRequest.model_validate(
        {"survey": _survey(), "human_facts": [fact]}
    )


def test_api_adapter_returns_derived_scene_input_without_mutating_source() -> None:
    request = _request()
    before = deepcopy(request.survey.model_dump())

    result = prepare_human_fact_scene_handoff(request)

    assert request.survey.model_dump() == before
    assert result.source_survey_id == request.survey.id
    assert result.scene_input_survey is not request.survey
    assert result.scene_input_survey.known_measurements == []
    assert result.human_facts[0].source.kind.value == "user_provided"
    assert result.scene_input_survey.observations[0].attributes["stair_topology"]["direction_change"] is True


def test_api_adapter_rejects_unknown_observation_instead_of_browser_side_guessing() -> None:
    with pytest.raises(ValueError, match="unknown observation"):
        prepare_human_fact_scene_handoff(_request(observation_id="missing-stair"))


def test_api_adapter_rejects_non_user_provenance() -> None:
    with pytest.raises(ValueError, match="user_provided"):
        _request(source={"kind": "inferred", "confidence": 0.7})
