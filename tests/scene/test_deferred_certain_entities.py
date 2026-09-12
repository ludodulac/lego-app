import copy
import json
from pathlib import Path

from brickhouse.scene import ArchitecturalScene, project_scene_to_building, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


FIXTURE = Path(__file__).parents[1] / "fixtures" / "generic_opening_pane_count_fidelity.json"


def _base_payloads():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    survey = copy.deepcopy(payload["survey"])
    scene = copy.deepcopy(payload["scene"])
    return survey, scene


def test_plausible_opening_type_may_remain_unknown_without_drift():
    survey, scene = _base_payloads()
    observation = survey["observations"][0]
    observation["attributes"]["semantic_type"] = "door_or_glazed_door"
    observation["attribute_certainty"] = {
        "physical_object_count": "certain",
        "semantic_type": "plausible",
    }
    scene["openings"][0]["type"] = "unknown"

    issues = validate_scene_against_survey(
        ArchitecturalSurvey.model_validate(survey),
        ArchitecturalScene.model_validate(scene),
    )
    assert not [issue for issue in issues if issue.code == "opening_type_drift"]


def test_certain_unresolved_opening_and_chimney_are_explicitly_deferred():
    survey, scene = _base_payloads()
    survey["observations"].extend([
        {
            "id": "certain-opening-unresolved",
            "kind": "opening",
            "certainty": "certain",
            "statement": "Opening existence is certain but facade is not resolved.",
            "evidence": [{"photo_index": 1, "observation": "Same physical opening is visible across views."}],
            "attributes": {"physical_object_count": 1},
            "attribute_certainty": {"physical_object_count": "certain"},
        },
        {
            "id": "certain-chimney-unresolved",
            "kind": "chimney",
            "certainty": "certain",
            "statement": "Chimney existence is certain but target ownership/geometry is unresolved.",
            "evidence": [{"photo_index": 1, "observation": "A chimney stack is visible near the roof."}],
            "attributes": {"subject_ownership": "unresolved"},
            "attribute_certainty": {"subject_ownership": "unproven"},
        },
    ])
    scene["deferred_entities"] = [
        {
            "survey_id": "certain-opening-unresolved",
            "kind": "opening",
            "geometry_status": "unresolved",
            "reason": "facade unresolved",
        },
        {
            "survey_id": "certain-chimney-unresolved",
            "kind": "chimney",
            "geometry_status": "unresolved",
            "reason": "ownership and geometry unresolved",
        },
    ]

    parsed_survey = ArchitecturalSurvey.model_validate(survey)
    parsed_scene = ArchitecturalScene.model_validate(scene)
    issues = validate_scene_against_survey(parsed_survey, parsed_scene)

    assert not [issue for issue in issues if issue.code == "certain_opening_missing" and issue.object_id == "certain-opening-unresolved"]
    assert not [issue for issue in issues if issue.code == "certain_chimney_missing"]

    projection = project_scene_to_building(parsed_scene)
    assert projection.blocked
    blocker_ids = {
        issue.object_id
        for issue in projection.issues
        if issue.code == "certain_entity_geometry_unresolved"
    }
    assert blocker_ids == {"certain-opening-unresolved", "certain-chimney-unresolved"}


def test_deferred_reference_cannot_duplicate_promoted_scene_primitive():
    _, scene = _base_payloads()
    scene["deferred_entities"] = [
        {
            "survey_id": scene["openings"][0]["id"],
            "kind": "opening",
            "geometry_status": "unresolved",
        }
    ]

    try:
        ArchitecturalScene.model_validate(scene)
    except ValueError as exc:
        assert "both deferred and promoted" in str(exc)
    else:
        raise AssertionError("duplicate promoted/deferred Survey id must be rejected")
