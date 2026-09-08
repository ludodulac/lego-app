from copy import deepcopy

import pytest

from brickhouse.building import SourceInfo, SourceKind
from brickhouse.survey.human_facts import HumanAttributeFact, apply_human_attribute_facts
from brickhouse.survey.models import ArchitecturalSurvey
from brickhouse.survey.stair_topology import analyze_survey_stair_topology


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(
        {
            "schema_version": "0.1",
            "id": "human-facts-test",
            "name": "Human facts test",
            "photos": [
                {
                    "photo_index": 1,
                    "facade": "front",
                    "description": "Exterior stair is visible but its turn is ambiguous in the photo.",
                    "source": {"kind": "observed", "confidence": 1.0},
                    "image_left_maps_to_facade_offset": "low",
                }
            ],
            "observations": [
                {
                    "id": "stair-system",
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


def _fact(**updates) -> HumanAttributeFact:
    payload = {
        "observation_id": "stair-system",
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


def test_user_fact_overlay_preserves_source_and_unlocks_existing_topology_reasoning() -> None:
    source = _survey()
    before = deepcopy(source.model_dump())

    application = apply_human_attribute_facts(source, [_fact()])

    assert source.model_dump() == before
    assert application.source_survey_id == source.id
    assert application.facts[0].source.kind is SourceKind.USER_PROVIDED
    assert application.candidate.known_measurements == []

    report = analyze_survey_stair_topology(application.candidate)
    assert report.issues == []
    assert len(report.facts) == 1
    assert report.facts[0].requires_multiple_scene_runs is True
    assert report.facts[0].topology.direction_change is True
    assert report.facts[0].topology.exact_run_count is None


def test_human_fact_requires_explicit_user_provenance() -> None:
    with pytest.raises(ValueError, match="source.kind=user_provided"):
        _fact(source={"kind": "inferred", "confidence": 1.0})


def test_conflicting_existing_attribute_requires_explicit_supersession() -> None:
    source = _survey()
    source.observations[0].attributes["stair_topology"] = {"direction_change": False}
    source.observations[0].attribute_certainty["stair_topology"] = "plausible"

    with pytest.raises(ValueError, match="supersedes_existing=true"):
        apply_human_attribute_facts(source, [_fact()])

    application = apply_human_attribute_facts(
        source,
        [_fact(supersedes_existing=True)],
    )
    assert application.candidate.observations[0].attributes["stair_topology"]["direction_change"] is True
    assert source.observations[0].attributes["stair_topology"]["direction_change"] is False


def test_unknown_observation_is_rejected_deterministically() -> None:
    with pytest.raises(ValueError, match="unknown observation"):
        apply_human_attribute_facts(
            _survey(),
            [_fact(observation_id="missing-stair")],
        )
