from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def base_survey(observation: dict) -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "survey_test",
        "name": "Survey test",
        "photos": [
            {
                "photo_index": 1,
                "facade": "front",
                "description": "front",
                "source": {"kind": "user_provided", "confidence": 0.99},
                "image_left_maps_to_facade_offset": "low",
            }
        ],
        "observations": [observation],
    })


def evidence() -> list[dict]:
    return [{"photo_index": 1, "observation": "visible"}]


def test_user_confirmed_opening_requires_stable_semantic_role() -> None:
    survey = base_survey({
        "id": "opening",
        "kind": "opening",
        "facade": "front",
        "certainty": "certain",
        "statement": "Low opening",
        "evidence": evidence(),
        "attributes": {"confirmed_by_user": True, "target_building_ownership": "proven"},
    })
    assert {issue.code for issue in validate_survey_semantics(survey)} == {"confirmed_opening_missing_semantic_role"}


def test_user_confirmed_workshop_window_can_keep_glass_block_glazing() -> None:
    survey = base_survey({
        "id": "workshop_window",
        "kind": "opening",
        "facade": "front",
        "certainty": "certain",
        "statement": "Workshop window",
        "evidence": evidence(),
        "attributes": {
            "confirmed_by_user": True,
            "semantic_role": "window",
            "room_role": "workshop",
            "target_building_ownership": "proven",
        },
        "opening_visual": {"glazing": "glass_blocks"},
    })
    assert validate_survey_semantics(survey) == []


def test_unproven_opening_ownership_cannot_be_plausible_target_opening() -> None:
    survey = base_survey({
        "id": "beyond_pole",
        "kind": "opening",
        "facade": "front",
        "certainty": "plausible",
        "statement": "Possible opening beyond boundary",
        "evidence": evidence(),
        "attributes": {"semantic_role": "window", "target_building_ownership": "unproven"},
    })
    assert {issue.code for issue in validate_survey_semantics(survey)} == {"opening_target_ownership_unproven"}


def test_gable_end_rejects_front_eave_terminology() -> None:
    survey = base_survey({
        "id": "roof",
        "kind": "roof",
        "facade": "front",
        "certainty": "certain",
        "statement": "Front gable",
        "evidence": evidence(),
        "attributes": {
            "facade_roof_relationship": "gable_end",
            "roof_edge_type": "eave_across_facade",
        },
    })
    assert {issue.code for issue in validate_survey_semantics(survey)} == {"gable_eave_terminology_conflict"}
