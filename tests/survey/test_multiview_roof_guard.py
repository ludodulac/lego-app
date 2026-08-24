from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def make_survey(*, evidence_count: int, attributes: dict | None = None, attribute_certainty: dict | None = None) -> ArchitecturalSurvey:
    photos = [
        {
            "photo_index": index,
            "facade": "front" if index == 1 else "left",
            "description": f"view {index}",
            "source": {"kind": "user_provided", "confidence": 0.99},
            "image_left_maps_to_facade_offset": "low",
        }
        for index in range(1, max(2, evidence_count) + 1)
    ]
    return ArchitecturalSurvey.model_validate(
        {
            "schema_version": "0.1",
            "id": "roof_guard",
            "name": "Roof guard",
            "photos": photos,
            "observations": [
                {
                    "id": "roof",
                    "kind": "roof",
                    "facade": "front",
                    "certainty": "certain",
                    "statement": "Roof is visible",
                    "evidence": [
                        {"photo_index": index, "observation": "roof visible"}
                        for index in range(1, evidence_count + 1)
                    ],
                    "attributes": attributes or {},
                    "attribute_certainty": attribute_certainty or {},
                }
            ],
        }
    )


def codes(survey: ArchitecturalSurvey) -> set[str]:
    return {issue.code for issue in validate_survey_semantics(survey)}


def test_multiview_roof_cannot_silently_lose_all_shape_hypotheses() -> None:
    assert "multiview_roof_missing_shape_hypothesis" in codes(
        make_survey(evidence_count=2)
    )


def test_single_view_roof_may_remain_shape_unknown() -> None:
    assert "multiview_roof_missing_shape_hypothesis" not in codes(
        make_survey(evidence_count=1)
    )


def test_plausible_gable_hypothesis_satisfies_guard_without_promotion() -> None:
    survey = make_survey(
        evidence_count=2,
        attributes={"roof_type": "gable"},
        attribute_certainty={"roof_type": "plausible"},
    )
    assert "multiview_roof_missing_shape_hypothesis" not in codes(survey)
    roof = survey.observations[0]
    assert roof.attributes["roof_type"] == "gable"
    assert roof.attribute_certainty["roof_type"].value == "plausible"
    assert "pitch_degrees" not in roof.attributes


def test_explicit_non_gable_hypothesis_is_preserved_as_valid_information() -> None:
    survey = make_survey(
        evidence_count=3,
        attributes={"facade_is_gable": False},
        attribute_certainty={"facade_is_gable": "plausible"},
    )
    assert "multiview_roof_missing_shape_hypothesis" not in codes(survey)
    assert survey.observations[0].attributes["facade_is_gable"] is False
