from copy import deepcopy

import pytest
from pydantic import ValidationError

from brickhouse.survey import ArchitecturalSurvey
from brickhouse.survey.human_spatial_facts import HumanRelativeLevelFact, validate_human_relative_level_facts

SOURCE = {"kind": "observed", "confidence": 1.0}
USER = {"kind": "user_provided", "confidence": 1.0}

def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1", "id": "generic-level-survey", "name": "Generic level survey",
        "photos": [{"photo_index": 1, "facade": "front", "description": "Canonical context view.", "source": SOURCE, "image_left_maps_to_facade_offset": "low"}],
        "known_measurements": [],
        "observations": [
            {"id": "deck-a", "kind": "platform", "certainty": "certain", "statement": "First platform.", "evidence": [{"photo_index": 1, "observation": "First platform visible."}]},
            {"id": "landing-b", "kind": "platform", "certainty": "certain", "statement": "Second platform.", "evidence": [{"photo_index": 1, "observation": "Second platform visible."}]},
        ],
    })

def _fact(subject="deck-a", object="landing-b", relation="lower_than") -> HumanRelativeLevelFact:
    return HumanRelativeLevelFact.model_validate({
        "subject_observation_id": subject, "object_observation_id": object, "relation": relation,
        "certainty": "certain", "source": USER, "statement": "User confirms qualitative relative level only.",
    })

def test_relative_level_fact_is_non_destructive_and_non_metric() -> None:
    survey = _survey(); before = deepcopy(survey.model_dump())
    result = validate_human_relative_level_facts(survey, [_fact()])
    assert result.source_survey_id == survey.id
    assert result.facts[0].relation == "lower_than"
    assert survey.model_dump() == before
    assert survey.known_measurements == []
    assert "delta" not in result.facts[0].model_dump()

def test_relative_level_fact_requires_user_provenance_and_existing_ids() -> None:
    payload = _fact().model_dump(mode="json"); payload["source"] = {"kind": "inferred", "confidence": 0.8}
    with pytest.raises(ValidationError, match="source.kind=user_provided"):
        HumanRelativeLevelFact.model_validate(payload)
    with pytest.raises(ValueError, match="unknown observation"):
        validate_human_relative_level_facts(_survey(), [_fact(subject="missing")])

def test_self_duplicate_inverse_and_same_level_conflicts_are_rejected() -> None:
    with pytest.raises(ValidationError, match="subject and object must differ"):
        _fact(subject="deck-a", object="deck-a")
    with pytest.raises(ValueError, match="duplicate"):
        validate_human_relative_level_facts(_survey(), [_fact(), _fact()])
    with pytest.raises(ValueError, match="contradictory inverse"):
        validate_human_relative_level_facts(_survey(), [_fact(), _fact(subject="landing-b", object="deck-a", relation="lower_than")])
    with pytest.raises(ValueError, match="contradict same_level"):
        validate_human_relative_level_facts(_survey(), [_fact(), _fact(relation="same_level")])
