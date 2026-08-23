from brickhouse.survey import ArchitecturalSurvey, validate_survey_extension, validate_survey_semantics


def _base_survey(*, certainty: str = "plausible") -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "adaptive-capture-survey",
        "name": "Adaptive capture survey",
        "photos": [
            {
                "photo_index": 1,
                "facade": "left",
                "description": "Oblique view of an exterior circulation zone",
                "source": {"kind": "observed", "confidence": 0.8},
            }
        ],
        "observations": [
            {
                "id": "stair-hypothesis-1",
                "kind": "stair",
                "facade": "left",
                "certainty": certainty,
                "statement": "A stair run is visible but its upper connection is partly hidden.",
                "evidence": [{"photo_index": 1, "observation": "Lower stair visible; upper end disappears behind a wall."}],
                "attributes": {
                    "architectural_kind": "stair",
                    "target_building_ownership": "proven",
                },
            }
        ],
    })


def _extended(base: ArchitecturalSurvey, *, new_photo_index: int = 2) -> ArchitecturalSurvey:
    data = base.model_dump(mode="json")
    data["photos"].append({
        "photo_index": new_photo_index,
        "facade": "left",
        "description": "Second angle exposing the previously hidden upper stair connection",
        "source": {"kind": "observed", "confidence": 0.95},
    })
    data["observations"].append({
        "id": "stair-refinement-2",
        "kind": "stair",
        "facade": "left",
        "certainty": "certain",
        "statement": "The second angle proves the upper stair run terminates at the side landing.",
        "evidence": [{"photo_index": new_photo_index, "observation": "Upper stair endpoint and landing edge are simultaneously visible."}],
        "attributes": {
            "architectural_kind": "stair",
            "target_building_ownership": "proven",
            "refines_observation_id": "stair-hypothesis-1",
        },
    })
    return ArchitecturalSurvey.model_validate(data)


def test_new_photo_can_refine_uncertain_observation_without_rewriting_history() -> None:
    base = _base_survey(certainty="plausible")
    candidate = _extended(base)
    issues = validate_survey_extension(base, candidate)
    assert issues == []
    assert candidate.observations[0] == base.observations[0]
    assert candidate.observations[1].attributes["refines_observation_id"] == "stair-hypothesis-1"


def test_certain_observation_requires_explicit_correction_not_photo_refinement() -> None:
    base = _base_survey(certainty="certain")
    candidate = _extended(base)
    codes = {issue.code for issue in validate_survey_extension(base, candidate)}
    assert "certain_observation_cannot_be_refined" in codes


def test_refinement_must_add_independent_photo_evidence() -> None:
    base = _base_survey(certainty="plausible")
    data = base.model_dump(mode="json")
    data["observations"].append({
        "id": "stair-refinement-without-new-view",
        "kind": "stair",
        "facade": "left",
        "certainty": "certain",
        "statement": "Unsupported re-interpretation of the same image.",
        "evidence": [{"photo_index": 1, "observation": "Same original view."}],
        "attributes": {
            "architectural_kind": "stair",
            "target_building_ownership": "proven",
            "refines_observation_id": "stair-hypothesis-1",
        },
    })
    candidate = ArchitecturalSurvey.model_validate(data)
    codes = {issue.code for issue in validate_survey_semantics(candidate)}
    assert "refinement_without_new_evidence" in codes
