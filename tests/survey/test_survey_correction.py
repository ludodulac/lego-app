from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from brickhouse.survey import (
    ArchitecturalSurvey,
    KnownMeasurement,
    SurveyAudit,
    SurveyCorrection,
    SurveyObservation,
    validate_survey_correction,
)


FIXTURE = Path(__file__).parents[1] / "fixtures" / "architectural_survey_real_house_photos_1_2.json"


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _missing_roof_audit(survey: ArchitecturalSurvey) -> SurveyAudit:
    return SurveyAudit.model_validate(
        {
            "schema_version": "0.1",
            "kind": "survey_audit",
            "survey_id": survey.id,
            "summary": {"status": "needs_correction", "issue_count": 1},
            "findings": [
                {
                    "id": "audit-missing-roof",
                    "status": "missing",
                    "target_type": "survey",
                    "target_id": None,
                    "severity": "error",
                    "photo_evidence": [
                        {"photo_index": 1, "observation": "Roof edge visible."}
                    ],
                    "message": "A visible roof observation is missing.",
                    "suggested_action": "add",
                }
            ],
        }
    )


def _roof_observation(item_id: str = "audit-added-roof") -> SurveyObservation:
    return SurveyObservation.model_validate(
        {
            "id": item_id,
            "kind": "roof",
            "facade": "front",
            "certainty": "certain",
            "statement": "A roof edge is visible above the front facade.",
            "evidence": [
                {"photo_index": 1, "observation": "Visible roof edge."}
            ],
            "attributes": {"roof_edge_type": "rake_or_gable_edge"},
            "attribute_certainty": {"roof_edge_type": "plausible"},
        }
    )


def _add_correction(
    survey: ArchitecturalSurvey,
    *,
    candidate: ArchitecturalSurvey | None = None,
) -> SurveyCorrection:
    candidate = candidate or survey.model_copy(deep=True)
    if not any(item.id == "audit-added-roof" for item in candidate.observations):
        candidate.observations.append(_roof_observation())
    return SurveyCorrection.model_validate(
        {
            "schema_version": "0.1",
            "kind": "survey_correction",
            "survey_id": survey.id,
            "candidate": candidate,
            "changes": [
                {
                    "id": "change-add-roof",
                    "finding_id": "audit-missing-roof",
                    "object_type": "observation",
                    "source_id": None,
                    "candidate_id": "audit-added-roof",
                    "action": "add",
                    "message": "Add only the roof observation supported by the audit.",
                }
            ],
        }
    )


def test_survey_correction_accepts_declared_audit_linked_addition() -> None:
    survey = _survey()
    original = survey.model_dump(mode="json")
    audit = _missing_roof_audit(survey)
    correction = _add_correction(survey)

    assert validate_survey_correction(survey, audit, correction) == []
    assert survey.model_dump(mode="json") == original
    assert correction.candidate.id == survey.id


def test_survey_correction_rejects_undeclared_extra_change() -> None:
    survey = _survey()
    audit = _missing_roof_audit(survey)
    candidate = survey.model_copy(deep=True)
    candidate.observations.extend(
        [
            _roof_observation(),
            SurveyObservation.model_validate(
                {
                    "id": "undeclared-chimney",
                    "kind": "chimney",
                    "facade": "front",
                    "certainty": "plausible",
                    "statement": "A chimney-like element is visible.",
                    "evidence": [
                        {"photo_index": 1, "observation": "Vertical roof element."}
                    ],
                    "attributes": {},
                    "attribute_certainty": {},
                }
            ),
        ]
    )
    correction = _add_correction(survey, candidate=candidate)

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert "survey_correction_undeclared_addition" in codes


def test_survey_correction_freezes_user_measurements() -> None:
    survey = _survey()
    survey.known_measurements.append(
        KnownMeasurement.model_validate(
            {
                "kind": "front_width",
                "value": 10.0,
                "units": "m",
                "source": {"kind": "user_provided", "confidence": 1.0},
            }
        )
    )
    audit = _missing_roof_audit(survey)
    candidate = survey.model_copy(deep=True)
    candidate.observations.append(_roof_observation())
    candidate.known_measurements[0].value = 11.0
    correction = _add_correction(survey, candidate=candidate)

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert "survey_correction_frozen_known_measurements_changed" in codes


def test_survey_correction_rejects_review_as_direct_mutation() -> None:
    with pytest.raises(ValidationError, match="cannot directly mutate"):
        SurveyCorrection.model_validate(
            {
                "schema_version": "0.1",
                "kind": "survey_correction",
                "survey_id": "survey",
                "candidate": _survey(),
                "changes": [
                    {
                        "id": "change-review",
                        "finding_id": "audit-review",
                        "object_type": "observation",
                        "source_id": "opening",
                        "candidate_id": "opening",
                        "action": "review",
                        "message": "Review only.",
                    }
                ],
            }
        )


def test_survey_correction_candidate_must_still_pass_survey_semantics() -> None:
    survey = _survey()
    target = next(item for item in survey.observations if item.kind.value == "opening")
    audit = SurveyAudit.model_validate(
        {
            "schema_version": "0.1",
            "kind": "survey_audit",
            "survey_id": survey.id,
            "summary": {"status": "needs_correction", "issue_count": 1},
            "findings": [
                {
                    "id": "audit-opening-orientation",
                    "status": "disputed",
                    "target_type": "observation",
                    "target_id": target.id,
                    "severity": "warning",
                    "photo_evidence": [
                        {"photo_index": 1, "observation": "Opening visible."}
                    ],
                    "message": "Opening orientation needs correction.",
                    "suggested_action": "reorient",
                }
            ],
        }
    )
    candidate = survey.model_copy(deep=True)
    candidate_target = next(item for item in candidate.observations if item.id == target.id)
    candidate_target.attributes["physical_object_count"] = 2
    correction = SurveyCorrection.model_validate(
        {
            "schema_version": "0.1",
            "kind": "survey_correction",
            "survey_id": survey.id,
            "candidate": candidate,
            "changes": [
                {
                    "id": "change-opening-orientation",
                    "finding_id": "audit-opening-orientation",
                    "object_type": "observation",
                    "source_id": target.id,
                    "candidate_id": target.id,
                    "action": "reorient",
                    "message": "Attempt an in-place correction.",
                }
            ],
        }
    )

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert "survey_correction_candidate_opening_not_single_physical_object" in codes
