from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from brickhouse.survey import (
    ArchitecturalSurvey,
    Certainty,
    SurveyAudit,
    SurveyCorrection,
    validate_survey_correction,
)


FIXTURE = Path(__file__).parents[1] / "fixtures" / "architectural_survey_real_house_photos_1_2.json"


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _audit(
    survey: ArchitecturalSurvey,
    *,
    finding_id: str,
    target_id: str,
    action: str,
) -> SurveyAudit:
    return SurveyAudit.model_validate(
        {
            "schema_version": "0.1",
            "kind": "survey_audit",
            "survey_id": survey.id,
            "summary": {"status": "needs_correction", "issue_count": 1},
            "findings": [
                {
                    "id": finding_id,
                    "status": "disputed",
                    "target_type": "observation",
                    "target_id": target_id,
                    "severity": "warning",
                    "photo_evidence": [
                        {"photo_index": 1, "observation": "Target visible in the source photo."}
                    ],
                    "message": "Audit-linked correction required.",
                    "suggested_action": action,
                }
            ],
        }
    )


def _correction(
    survey: ArchitecturalSurvey,
    audit: SurveyAudit,
    candidate: ArchitecturalSurvey,
    *,
    change_id: str,
    target_id: str,
    action: str,
    candidate_id: str | None = None,
) -> SurveyCorrection:
    return SurveyCorrection.model_validate(
        {
            "schema_version": "0.1",
            "kind": "survey_correction",
            "survey_id": survey.id,
            "candidate": candidate,
            "changes": [
                {
                    "id": change_id,
                    "finding_id": audit.findings[0].id,
                    "object_type": "observation",
                    "source_id": target_id,
                    "candidate_id": candidate_id if candidate_id is not None else target_id,
                    "action": action,
                    "message": "Apply only the audited action.",
                }
            ],
        }
    )


def _photo_audit(
    survey: ArchitecturalSurvey,
    *,
    photo_index: int,
    finding_id: str = "audit-reorient-photo",
) -> SurveyAudit:
    return SurveyAudit.model_validate(
        {
            "schema_version": "0.1",
            "kind": "survey_audit",
            "survey_id": survey.id,
            "summary": {"status": "needs_correction", "issue_count": 1},
            "findings": [
                {
                    "id": finding_id,
                    "status": "disputed",
                    "target_type": "photo",
                    "target_id": str(photo_index),
                    "severity": "warning",
                    "photo_evidence": [
                        {
                            "photo_index": photo_index,
                            "observation": "Human-confirmed facade orientation contradicts the capture hint.",
                        }
                    ],
                    "message": "Reorient this photo only.",
                    "suggested_action": "reorient",
                }
            ],
        }
    )


def _photo_correction(
    survey: ArchitecturalSurvey,
    audit: SurveyAudit,
    candidate: ArchitecturalSurvey,
    *,
    source_id: str,
) -> SurveyCorrection:
    return SurveyCorrection.model_validate(
        {
            "schema_version": "0.1",
            "kind": "survey_correction",
            "survey_id": survey.id,
            "candidate": candidate,
            "changes": [
                {
                    "id": f"change-reorient-photo-{source_id}",
                    "finding_id": audit.findings[0].id,
                    "object_type": "photo",
                    "source_id": source_id,
                    "candidate_id": source_id,
                    "action": "reorient",
                    "message": "Apply only the audited photo orientation correction.",
                }
            ],
        }
    )


def test_lower_certainty_accepts_only_a_real_certainty_decrease() -> None:
    survey = _survey()
    target_id = "front_upper_left_window"
    audit = _audit(
        survey,
        finding_id="audit-lower-window-certainty",
        target_id=target_id,
        action="lower_certainty",
    )
    candidate = survey.model_copy(deep=True)
    target = next(item for item in candidate.observations if item.id == target_id)
    target.certainty = Certainty.PLAUSIBLE
    correction = _correction(
        survey,
        audit,
        candidate,
        change_id="change-lower-window-certainty",
        target_id=target_id,
        action="lower_certainty",
    )

    assert validate_survey_correction(survey, audit, correction) == []


def test_lower_certainty_rejects_semantic_mutation_hidden_in_same_change() -> None:
    survey = _survey()
    target_id = "front_upper_left_window"
    audit = _audit(
        survey,
        finding_id="audit-lower-window-certainty",
        target_id=target_id,
        action="lower_certainty",
    )
    candidate = survey.model_copy(deep=True)
    target = next(item for item in candidate.observations if item.id == target_id)
    target.certainty = Certainty.PLAUSIBLE
    target.attributes["semantic_type"] = "door"
    correction = _correction(
        survey,
        audit,
        candidate,
        change_id="change-lower-window-certainty",
        target_id=target_id,
        action="lower_certainty",
    )

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert "survey_correction_lower_certainty_scope_violation" in codes


def test_reorient_accepts_facade_rank_change_without_semantic_rewrite() -> None:
    survey = _survey()
    target_id = "front_upper_left_window"
    audit = _audit(
        survey,
        finding_id="audit-reorient-window",
        target_id=target_id,
        action="reorient",
    )
    candidate = survey.model_copy(deep=True)
    target = next(item for item in candidate.observations if item.id == target_id)
    target.attributes["facade_horizontal_rank"] = 3
    correction = _correction(
        survey,
        audit,
        candidate,
        change_id="change-reorient-window",
        target_id=target_id,
        action="reorient",
    )

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert not {code for code in codes if code.startswith("survey_correction_reorient_")}


def test_reorient_rejects_non_orientation_attribute_change() -> None:
    survey = _survey()
    target_id = "front_upper_left_window"
    audit = _audit(
        survey,
        finding_id="audit-reorient-window",
        target_id=target_id,
        action="reorient",
    )
    candidate = survey.model_copy(deep=True)
    target = next(item for item in candidate.observations if item.id == target_id)
    target.attributes["facade_horizontal_rank"] = 3
    target.attributes["semantic_type"] = "door"
    correction = _correction(
        survey,
        audit,
        candidate,
        change_id="change-reorient-window",
        target_id=target_id,
        action="reorient",
    )

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert "survey_correction_reorient_non_orientation_attribute_changed" in codes


def test_photo_reorient_accepts_only_orientation_change_and_preserves_source() -> None:
    survey = _survey()
    original_photo = survey.photos[1].model_copy(deep=True)
    candidate = survey.model_copy(deep=True)
    candidate.photos[1] = candidate.photos[1].model_copy(update={"facade": "rear"})
    audit = _photo_audit(survey, photo_index=2)
    correction = _photo_correction(survey, audit, candidate, source_id="2")

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert not {code for code in codes if code.startswith("survey_correction_photo_reorient_")}
    assert "survey_correction_source_target_mismatch" not in codes
    assert survey.photos[1] == original_photo
    assert survey.photos[1].facade != candidate.photos[1].facade


def test_photo_reorient_rejects_hidden_description_change() -> None:
    survey = _survey()
    candidate = survey.model_copy(deep=True)
    candidate.photos[1] = candidate.photos[1].model_copy(
        update={"facade": "rear", "description": "Rewritten semantic content."}
    )
    audit = _photo_audit(survey, photo_index=2)
    correction = _photo_correction(survey, audit, candidate, source_id="2")

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert "survey_correction_photo_reorient_scope_violation" in codes


def test_photo_reorient_requires_same_audited_photo() -> None:
    survey = _survey()
    candidate = survey.model_copy(deep=True)
    candidate.photos[1] = candidate.photos[1].model_copy(update={"facade": "rear"})
    audit = _photo_audit(survey, photo_index=2)
    correction = _photo_correction(survey, audit, candidate, source_id="1")

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert "survey_correction_source_target_mismatch" in codes
    assert "survey_correction_undeclared_modification" in codes


def test_photo_correction_schema_rejects_non_reorient_actions() -> None:
    survey = _survey()
    candidate = survey.model_copy(deep=True)
    audit = _photo_audit(survey, photo_index=2)

    with pytest.raises(ValidationError, match="photo corrections support reorient only"):
        SurveyCorrection.model_validate(
            {
                "schema_version": "0.1",
                "kind": "survey_correction",
                "survey_id": survey.id,
                "candidate": candidate,
                "changes": [
                    {
                        "id": "change-remove-photo-2",
                        "finding_id": audit.findings[0].id,
                        "object_type": "photo",
                        "source_id": "2",
                        "candidate_id": None,
                        "action": "remove",
                        "message": "Not allowed.",
                    }
                ],
            }
        )


def test_merge_remains_manual_review_only_in_v01() -> None:
    survey = _survey()
    source_id = "front_upper_left_window"
    target_id = "front_upper_right_window"
    audit = _audit(
        survey,
        finding_id="audit-duplicate-window",
        target_id=source_id,
        action="merge",
    )
    candidate = survey.model_copy(deep=True)
    candidate.observations = [item for item in candidate.observations if item.id != source_id]
    correction = _correction(
        survey,
        audit,
        candidate,
        change_id="change-merge-window",
        target_id=source_id,
        candidate_id=target_id,
        action="merge",
    )

    codes = {issue.code for issue in validate_survey_correction(survey, audit, correction)}
    assert "survey_correction_merge_requires_manual_review" in codes
