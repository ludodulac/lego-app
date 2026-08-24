from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

SOURCE = {"kind": "observed", "confidence": 0.9}


def _survey(horizontal_rank=1, vertical_rank=2) -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "opening-rank-survey",
        "name": "Opening rank survey",
        "photos": [{"photo_index": 1, "facade": "front", "description": "front", "source": SOURCE}],
        "observations": [{
            "id": "window-a",
            "kind": "opening",
            "facade": "front",
            "certainty": "certain",
            "statement": "window visible",
            "evidence": [{"photo_index": 1, "observation": "window visible"}],
            "attributes": {
                "physical_object_count": 1,
                "semantic_type": "window",
                "facade_horizontal_rank": horizontal_rank,
                "facade_vertical_rank": vertical_rank,
            },
        }],
    })


def test_positive_integer_layout_ranks_are_valid() -> None:
    codes = {issue.code for issue in validate_survey_semantics(_survey())}
    assert "invalid_opening_layout_rank" not in codes


def test_text_or_zero_layout_rank_is_rejected() -> None:
    text_codes = {issue.code for issue in validate_survey_semantics(_survey(horizontal_rank="left"))}
    zero_codes = {issue.code for issue in validate_survey_semantics(_survey(vertical_rank=0))}
    assert "invalid_opening_layout_rank" in text_codes
    assert "invalid_opening_layout_rank" in zero_codes


def test_boolean_is_not_accepted_as_integer_rank() -> None:
    codes = {issue.code for issue in validate_survey_semantics(_survey(horizontal_rank=True))}
    assert "invalid_opening_layout_rank" in codes
