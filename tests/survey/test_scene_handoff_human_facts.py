from copy import deepcopy

import pytest

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.survey.human_facts import HumanAttributeFact
from brickhouse.survey.models import ArchitecturalSurvey
from brickhouse.survey.scene_handoff import build_scene_handoff_with_human_facts
from brickhouse.survey.stair_topology import analyze_survey_stair_topology


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(
        {
            "schema_version": "0.1",
            "id": "generic-courtyard-house",
            "name": "Generic courtyard house",
            "photos": [
                {
                    "photo_index": 1,
                    "facade": "left",
                    "description": "An exterior access assembly is visible.",
                    "source": {"kind": "observed", "confidence": 1.0},
                    "image_left_maps_to_facade_offset": "low",
                }
            ],
            "known_measurements": [],
            "observations": [
                {
                    "id": "access-stair",
                    "kind": "stair",
                    "certainty": "certain",
                    "statement": "Exterior stair exists.",
                    "evidence": [
                        {"photo_index": 1, "observation": "Exterior stair is visible."}
                    ],
                }
            ],
        }
    )


def _turn_fact(**updates) -> HumanAttributeFact:
    payload = {
        "observation_id": "access-stair",
        "attribute_name": "stair_topology",
        "value": {
            "minimum_run_count": 2,
            "direction_change": True,
            "turning_node_kind": "turn_or_landing",
        },
        "certainty": "certain",
        "source": SourceInfo(kind=SourceKind.USER_PROVIDED, confidence=1.0),
        "statement": "User confirms that the stair changes direction.",
    }
    payload.update(updates)
    return HumanAttributeFact.model_validate(payload)


def test_handoff_preserves_accepted_survey_and_carries_user_fact_provenance() -> None:
    accepted = _survey()
    before = deepcopy(accepted.model_dump())

    handoff = build_scene_handoff_with_human_facts(accepted, [_turn_fact()])

    assert accepted.model_dump() == before
    assert handoff.source_survey_id == accepted.id
    assert handoff.human_facts[0].source.kind is SourceKind.USER_PROVIDED
    assert handoff.scene_input_survey.known_measurements == []

    topology = analyze_survey_stair_topology(handoff.scene_input_survey)
    assert topology.issues == []
    assert topology.facts[0].requires_multiple_scene_runs is True
    assert topology.facts[0].topology.direction_change is True


def test_handoff_rejects_unknown_target_through_existing_human_fact_contract() -> None:
    with pytest.raises(ValueError, match="unknown observation"):
        build_scene_handoff_with_human_facts(
            _survey(),
            [_turn_fact(observation_id="missing-object")],
        )


def test_handoff_rejects_conflicting_fact_without_explicit_supersession() -> None:
    accepted = _survey()
    accepted.observations[0].attributes["stair_topology"] = {"direction_change": False}
    accepted.observations[0].attribute_certainty["stair_topology"] = "plausible"

    with pytest.raises(ValueError, match="supersedes_existing=true"):
        build_scene_handoff_with_human_facts(accepted, [_turn_fact()])

    handoff = build_scene_handoff_with_human_facts(
        accepted,
        [_turn_fact(supersedes_existing=True)],
    )
    assert handoff.scene_input_survey.observations[0].attributes["stair_topology"]["direction_change"] is True
    assert accepted.observations[0].attributes["stair_topology"]["direction_change"] is False


def test_handoff_never_turns_semantic_fact_into_known_measurement() -> None:
    accepted = _survey()
    fact = HumanAttributeFact.model_validate(
        {
            "observation_id": "access-stair",
            "attribute_name": "material",
            "value": "masonry",
            "certainty": "certain",
            "source": {"kind": "user_provided", "confidence": 1.0},
            "statement": "User confirms the visible stair is masonry.",
        }
    )

    handoff = build_scene_handoff_with_human_facts(accepted, [fact])

    assert handoff.scene_input_survey.known_measurements == []
    assert handoff.scene_input_survey.observations[0].attributes["material"] == "masonry"
