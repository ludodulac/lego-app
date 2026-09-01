from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from brickhouse.survey import ArchitecturalSurvey, SurveyCorrection
from brickhouse.survey.correction_reaudit_contract import (
    SurveyCorrectionReaudit,
    validate_survey_correction_reaudit,
)


FIXTURE = Path(__file__).parents[1] / "fixtures" / "architectural_survey_real_house_photos_1_2.json"


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _correction(survey: ArchitecturalSurvey) -> SurveyCorrection:
    candidate = survey.model_copy(deep=True)
    target = next(item for item in candidate.observations if item.id == "front_upper_left_window")
    target.attributes["facade_horizontal_rank"] = 3
    return SurveyCorrection.model_validate(
        {
            "survey_id": survey.id,
            "candidate": candidate,
            "changes": [
                {
                    "id": "change-reorient-window",
                    "finding_id": "audit-reorient-window",
                    "object_type": "observation",
                    "source_id": "front_upper_left_window",
                    "candidate_id": "front_upper_left_window",
                    "action": "reorient",
                    "message": "Reorient the audited opening.",
                }
            ],
        }
    )


def test_targeted_reaudit_accepts_clean_pass_for_exact_change_scope() -> None:
    survey = _survey()
    correction = _correction(survey)
    reaudit = SurveyCorrectionReaudit.model_validate(
        {
            "survey_id": survey.id,
            "correction_change_ids": ["change-reorient-window"],
            "summary": {"status": "pass", "issue_count": 0},
            "findings": [],
        }
    )

    assert validate_survey_correction_reaudit(survey, correction, reaudit) == []


def test_targeted_reaudit_accepts_in_scope_candidate_finding() -> None:
    survey = _survey()
    correction = _correction(survey)
    reaudit = SurveyCorrectionReaudit.model_validate(
        {
            "survey_id": survey.id,
            "correction_change_ids": ["change-reorient-window"],
            "summary": {"status": "needs_correction", "issue_count": 1},
            "findings": [
                {
                    "id": "reaudit-window-still-wrong",
                    "status": "disputed",
                    "target_type": "observation",
                    "target_id": "front_upper_left_window",
                    "severity": "warning",
                    "photo_evidence": [
                        {"photo_index": 1, "observation": "The corrected rank remains inconsistent."}
                    ],
                    "message": "The corrected orientation is still not visually supported.",
                    "suggested_action": "review",
                }
            ],
        }
    )

    assert validate_survey_correction_reaudit(survey, correction, reaudit) == []


def test_targeted_reaudit_rejects_scope_expansion() -> None:
    survey = _survey()
    correction = _correction(survey)
    reaudit = SurveyCorrectionReaudit.model_validate(
        {
            "survey_id": survey.id,
            "correction_change_ids": ["change-reorient-window"],
            "summary": {"status": "needs_correction", "issue_count": 1},
            "findings": [
                {
                    "id": "reaudit-unrelated-window",
                    "status": "disputed",
                    "target_type": "observation",
                    "target_id": "front_upper_right_window",
                    "severity": "warning",
                    "photo_evidence": [
                        {"photo_index": 2, "observation": "Unrelated evidence."}
                    ],
                    "message": "This unrelated observation should require a fresh audit.",
                    "suggested_action": "review",
                }
            ],
        }
    )

    codes = {issue.code for issue in validate_survey_correction_reaudit(survey, correction, reaudit)}
    assert "survey_correction_reaudit_observation_out_of_scope" in codes
    assert "survey_correction_reaudit_photo_out_of_scope" in codes


def test_targeted_reaudit_requires_exact_correction_change_ids() -> None:
    survey = _survey()
    correction = _correction(survey)
    reaudit = SurveyCorrectionReaudit.model_validate(
        {
            "survey_id": survey.id,
            "correction_change_ids": ["different-change"],
            "summary": {"status": "pass", "issue_count": 0},
            "findings": [],
        }
    )

    codes = {issue.code for issue in validate_survey_correction_reaudit(survey, correction, reaudit)}
    assert "survey_correction_reaudit_change_scope_mismatch" in codes


def test_targeted_reaudit_status_cannot_claim_needs_correction_without_findings() -> None:
    with pytest.raises(ValidationError, match="requires at least one finding"):
        SurveyCorrectionReaudit.model_validate(
            {
                "survey_id": "survey",
                "correction_change_ids": ["change"],
                "summary": {"status": "needs_correction", "issue_count": 0},
                "findings": [],
            }
        )
