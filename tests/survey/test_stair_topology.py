from copy import deepcopy

from brickhouse.survey import (
    ArchitecturalSurvey,
    analyze_survey_stair_topology,
    validate_survey_semantics,
)


def make_survey(*, topology: dict, topology_certainty: str = "certain", extras: list[dict] | None = None) -> ArchitecturalSurvey:
    observations = [
        {
            "id": "stair-system",
            "kind": "stair",
            "certainty": "certain",
            "statement": "Exterior stair system is visible",
            "evidence": [
                {"photo_index": 1, "observation": "lower stair portion visible"},
                {"photo_index": 2, "observation": "upper stair portion and direction change visible"},
            ],
            "attributes": {"stair_topology": topology},
            "attribute_certainty": {"stair_topology": topology_certainty},
        }
    ]
    observations.extend(extras or [])
    return ArchitecturalSurvey.model_validate(
        {
            "schema_version": "0.1",
            "id": "stair-topology-test",
            "name": "Stair topology test",
            "photos": [
                {
                    "photo_index": 1,
                    "facade": "front",
                    "description": "front reference",
                    "source": {"kind": "user_provided", "confidence": 0.99},
                    "image_left_maps_to_facade_offset": "low",
                },
                {
                    "photo_index": 2,
                    "facade": "rear",
                    "description": "rear stair view",
                    "source": {"kind": "user_provided", "confidence": 0.99},
                    "image_left_maps_to_facade_offset": "low",
                },
            ],
            "observations": observations,
        }
    )


def test_direction_change_requires_multiple_scene_runs_without_fake_metrics() -> None:
    survey = make_survey(
        topology={
            "minimum_run_count": 2,
            "direction_change": True,
            "turning_node_kind": "turn_or_landing",
        }
    )

    report = analyze_survey_stair_topology(survey)

    assert report.issues == []
    assert len(report.facts) == 1
    fact = report.facts[0]
    assert fact.observation_id == "stair-system"
    assert fact.requires_multiple_scene_runs is True
    assert fact.topology.minimum_run_count == 2
    assert fact.topology.exact_run_count is None
    assert fact.topology.direction_change is True
    assert not hasattr(fact.topology, "run_length")
    assert not hasattr(fact.topology, "turn_coordinate")


def test_direction_change_alone_logically_blocks_single_run_collapse() -> None:
    survey = make_survey(topology={"direction_change": True})

    fact = analyze_survey_stair_topology(survey).facts[0]

    assert fact.requires_multiple_scene_runs is True
    assert fact.topology.minimum_run_count is None
    assert fact.topology.exact_run_count is None


def test_topology_analysis_preserves_attribute_certainty_and_does_not_mutate_survey() -> None:
    survey = make_survey(
        topology={"minimum_run_count": 2, "direction_change": True},
        topology_certainty="plausible",
    )
    before = deepcopy(survey.model_dump())

    fact = analyze_survey_stair_topology(survey).facts[0]

    assert fact.certainty.value == "plausible"
    assert survey.model_dump() == before


def test_exact_single_run_cannot_claim_direction_change() -> None:
    survey = make_survey(topology={"exact_run_count": 1, "direction_change": True})

    codes = {issue.code for issue in validate_survey_semantics(survey)}

    assert "invalid_stair_topology" in codes


def test_exact_run_count_cannot_be_below_observed_minimum() -> None:
    survey = make_survey(topology={"minimum_run_count": 3, "exact_run_count": 2})

    codes = {issue.code for issue in validate_survey_semantics(survey)}

    assert "invalid_stair_topology" in codes


def test_component_ids_must_reference_stair_observations() -> None:
    survey = make_survey(
        topology={"minimum_run_count": 2, "component_run_ids": ["opening-1", "missing"]},
        extras=[
            {
                "id": "opening-1",
                "kind": "opening",
                "facade": "rear",
                "certainty": "certain",
                "statement": "Opening is visible",
                "evidence": [{"photo_index": 2, "observation": "opening visible"}],
            }
        ],
    )

    codes = {issue.code for issue in validate_survey_semantics(survey)}

    assert "stair_component_not_stair" in codes
    assert "stair_component_missing" in codes


def test_explicit_component_runs_can_remain_non_metric_survey_observations() -> None:
    components = [
        {
            "id": run_id,
            "kind": "stair",
            "certainty": "certain",
            "statement": f"Component {run_id} is visibly part of the stair system",
            "evidence": [{"photo_index": 2, "observation": f"{run_id} visible"}],
        }
        for run_id in ("run-a", "run-b")
    ]
    survey = make_survey(
        topology={
            "minimum_run_count": 2,
            "direction_change": True,
            "component_run_ids": ["run-a", "run-b"],
        },
        extras=components,
    )

    report = analyze_survey_stair_topology(survey)

    assert report.issues == []
    assert report.facts[0].requires_multiple_scene_runs is True
    assert report.facts[0].topology.component_run_ids == ["run-a", "run-b"]
    for component in survey.observations[1:]:
        assert component.attributes == {}
