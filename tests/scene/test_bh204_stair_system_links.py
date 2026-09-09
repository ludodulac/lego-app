from copy import deepcopy

import pytest
from pydantic import ValidationError

from brickhouse.scene import (
    ArchitecturalScene,
    SceneStairSystemLink,
    analyze_multi_run_stair_geometry,
    validate_scene_against_survey,
)
from brickhouse.survey import ArchitecturalSurvey


SOURCE = {"kind": "inferred", "confidence": 0.8}


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(
        {
            "schema_version": "0.1",
            "id": "generic-parent-stair-survey",
            "name": "Generic parent stair survey",
            "photos": [
                {
                    "photo_index": 1,
                    "facade": "front",
                    "description": "Canonical context view.",
                    "source": {"kind": "observed", "confidence": 1.0},
                    "image_left_maps_to_facade_offset": "low",
                }
            ],
            "observations": [
                {
                    "id": "stair-system",
                    "kind": "stair",
                    "facade": "front",
                    "certainty": "certain",
                    "statement": "One semantic exterior stair system changes direction.",
                    "evidence": [{"photo_index": 1, "observation": "Turning stair system visible."}],
                    "attributes": {
                        "stair_topology": {
                            "minimum_run_count": 2,
                            "direction_change": True,
                            "turning_node_kind": "turn_or_landing"
                        }
                    },
                    "attribute_certainty": {"stair_topology": "certain"},
                },
                {
                    "id": "context-volume-observation",
                    "kind": "volume",
                    "facade": "front",
                    "certainty": "certain",
                    "statement": "A non-stair context volume.",
                    "evidence": [{"photo_index": 1, "observation": "Volume visible."}],
                },
            ],
        }
    )


def _scene(*, collinear: bool = False, only_one_link: bool = False, link_target: str = "stair-system") -> ArchitecturalScene:
    run_b_end = {"x": 4, "y": 0, "z": 2} if collinear else {"x": 2, "y": 2, "z": 2}
    links = [
        {
            "id": "link-run-a",
            "stair_run_id": "scene-run-a",
            "survey_stair_system_id": link_target,
            "source": SOURCE,
            "statement": "Metric run A derives from the semantic stair system.",
        }
    ]
    if not only_one_link:
        links.append(
            {
                "id": "link-run-b",
                "stair_run_id": "scene-run-b",
                "survey_stair_system_id": link_target,
                "source": SOURCE,
                "statement": "Metric run B derives from the semantic stair system.",
            }
        )
    host_position = {"x": run_b_end["x"], "y": run_b_end["y"], "z": 0}
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "generic-parent-stair-scene",
            "name": "Generic parent stair scene",
            "units": "m",
            "volumes": [
                {
                    "id": "host",
                    "position": host_position,
                    "width": {"value": 2, "source": SOURCE},
                    "depth": {"value": 2, "source": SOURCE},
                    "height": {"value": 4, "source": SOURCE},
                    "floors": 2,
                    "source": SOURCE,
                }
            ],
            "stairs": [
                {
                    "id": "scene-run-a",
                    "start": {"x": 0, "y": 0, "z": 0},
                    "end": {"x": 2, "y": 0, "z": 1},
                    "width": 1.0,
                    "source": SOURCE,
                },
                {
                    "id": "scene-run-b",
                    "start": {"x": 2, "y": 0, "z": 1},
                    "end": run_b_end,
                    "width": 1.0,
                    "source": SOURCE,
                },
            ],
            "stair_system_links": links,
            "appearance": {},
        }
    )


def _codes(survey: ArchitecturalSurvey, scene: ArchitecturalScene) -> set[str]:
    return {issue.code for issue in validate_scene_against_survey(survey, scene)}


def test_parent_linked_runs_realize_multi_run_topology_without_new_survey_observations() -> None:
    survey = _survey()
    survey_before = deepcopy(survey.model_dump())
    scene = _scene()

    fact = analyze_multi_run_stair_geometry(survey, scene).facts[0]
    codes = _codes(survey, scene)

    assert fact.component_run_ids == ["scene-run-a", "scene-run-b"]
    assert fact.all_components_present is True
    assert fact.connected is True
    assert fact.spanning_path_exists is True
    assert fact.direction_change_realized is True
    assert "certain_stair_missing" not in codes
    assert "certain_multiview_stair_not_geometrically_encoded" not in codes
    assert "scene_stair_not_in_survey" not in codes
    assert "multi_run_stair_topology_unresolved" not in codes
    assert "multi_run_stair_direction_change_not_realized" not in codes
    assert survey.model_dump() == survey_before


def test_too_few_parent_linked_runs_leave_topology_unresolved() -> None:
    survey = _survey()
    scene = _scene(only_one_link=True)

    assert "multi_run_stair_topology_unresolved" in _codes(survey, scene)
    fact = analyze_multi_run_stair_geometry(survey, scene).facts[0]
    assert fact.all_components_present is False


def test_parent_links_do_not_let_collinear_runs_fake_a_turn() -> None:
    survey = _survey()
    scene = _scene(collinear=True)

    assert "multi_run_stair_direction_change_not_realized" in _codes(survey, scene)


def test_parent_link_must_target_an_existing_survey_stair() -> None:
    survey = _survey()

    assert "stair_system_link_unknown_survey_observation" in _codes(
        survey, _scene(link_target="missing-stair")
    )
    assert "stair_system_link_source_not_stair" in _codes(
        survey, _scene(link_target="context-volume-observation")
    )


def test_scene_rejects_duplicate_or_unknown_run_links() -> None:
    payload = _scene().model_dump(mode="json")
    payload["stair_system_links"].append(
        {
            "id": "duplicate-link",
            "stair_run_id": "scene-run-a",
            "survey_stair_system_id": "stair-system",
            "source": SOURCE,
            "statement": "Second parent claim for same metric run.",
        }
    )
    with pytest.raises(ValidationError, match="more than one stair-system provenance link"):
        ArchitecturalScene.model_validate(payload)

    payload = _scene().model_dump(mode="json")
    payload["stair_system_links"][0]["stair_run_id"] = "missing-run"
    with pytest.raises(ValidationError, match="unknown Scene stair run"):
        ArchitecturalScene.model_validate(payload)


def test_generated_default_cannot_create_stair_system_provenance() -> None:
    with pytest.raises(ValidationError, match="cannot be generated_default"):
        SceneStairSystemLink.model_validate(
            {
                "id": "generated-link",
                "stair_run_id": "run",
                "survey_stair_system_id": "stair",
                "source": {"kind": "generated_default", "confidence": 0.4},
                "statement": "Unsafe default provenance.",
            }
        )
