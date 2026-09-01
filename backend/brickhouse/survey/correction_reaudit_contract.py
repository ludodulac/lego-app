"""Targeted diagnostic contract after a validated SurveyCorrection candidate.

A SurveyCorrectionReaudit never applies another mutation. It checks only the
bounded scope derived from one correction candidate and reports remaining or
new visual problems before that candidate can advance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .audit import (
    SurveyAuditFinding,
    SurveyAuditStatus,
    SurveyAuditSummary,
    SurveyAuditTargetType,
)
from .correction import SurveyCorrection
from .correction_reaudit import build_survey_correction_reaudit_scope
from .models import ArchitecturalSurvey


class SurveyCorrectionReaudit(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    kind: Literal["survey_correction_reaudit"] = "survey_correction_reaudit"
    survey_id: str = Field(min_length=1)
    correction_change_ids: list[str] = Field(min_length=1)
    summary: SurveyAuditSummary
    findings: list[SurveyAuditFinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_summary_and_change_ids(self) -> "SurveyCorrectionReaudit":
        if len(self.correction_change_ids) != len(set(self.correction_change_ids)):
            raise ValueError("correction_change_ids must be unique")
        if self.summary.issue_count != len(self.findings):
            raise ValueError("summary.issue_count must equal the number of findings")
        if self.summary.status is SurveyAuditStatus.PASS and self.findings:
            raise ValueError("pass re-audit cannot contain findings")
        if self.summary.status is SurveyAuditStatus.NEEDS_CORRECTION and not self.findings:
            raise ValueError("needs_correction re-audit requires at least one finding")
        return self


@dataclass(frozen=True)
class SurveyCorrectionReauditValidationIssue:
    code: str
    finding_id: str | None
    message: str
    severity: str = "error"


def validate_survey_correction_reaudit(
    original: ArchitecturalSurvey,
    correction: SurveyCorrection,
    reaudit: SurveyCorrectionReaudit,
) -> list[SurveyCorrectionReauditValidationIssue]:
    """Validate that a re-audit stays inside the deterministic correction scope."""
    issues: list[SurveyCorrectionReauditValidationIssue] = []
    candidate = correction.candidate
    scope = build_survey_correction_reaudit_scope(original, correction)

    if reaudit.survey_id != candidate.id:
        issues.append(
            SurveyCorrectionReauditValidationIssue(
                code="survey_correction_reaudit_survey_id_mismatch",
                finding_id=None,
                message="Re-audit survey_id must match the correction candidate Survey id.",
            )
        )

    if reaudit.correction_change_ids != scope.correction_change_ids:
        issues.append(
            SurveyCorrectionReauditValidationIssue(
                code="survey_correction_reaudit_change_scope_mismatch",
                finding_id=None,
                message=(
                    "Re-audit must cover exactly the correction change ids, in correction order."
                ),
            )
        )

    candidate_observations = {item.id for item in candidate.observations}
    candidate_relations = {item.id for item in candidate.relations}
    allowed_observations = set(scope.observation_ids) & candidate_observations
    allowed_relations = set(scope.relation_ids) & candidate_relations
    allowed_photos = set(scope.photo_indexes)
    known_candidate_photos = {photo.photo_index for photo in candidate.photos}

    finding_ids: set[str] = set()
    for finding in reaudit.findings:
        if finding.id in finding_ids:
            issues.append(
                SurveyCorrectionReauditValidationIssue(
                    code="survey_correction_reaudit_duplicate_finding_id",
                    finding_id=finding.id,
                    message=f"Duplicate re-audit finding id {finding.id!r}.",
                )
            )
        finding_ids.add(finding.id)

        if finding.target_type is SurveyAuditTargetType.OBSERVATION:
            if finding.target_id not in allowed_observations:
                issues.append(
                    SurveyCorrectionReauditValidationIssue(
                        code="survey_correction_reaudit_observation_out_of_scope",
                        finding_id=finding.id,
                        message=(
                            "Targeted re-audit observation findings must refer to a changed "
                            "candidate observation in the deterministic scope."
                        ),
                    )
                )
        elif finding.target_type is SurveyAuditTargetType.RELATION:
            if finding.target_id not in allowed_relations:
                issues.append(
                    SurveyCorrectionReauditValidationIssue(
                        code="survey_correction_reaudit_relation_out_of_scope",
                        finding_id=finding.id,
                        message=(
                            "Targeted re-audit relation findings must refer to an in-scope "
                            "candidate relation."
                        ),
                    )
                )
        else:
            issues.append(
                SurveyCorrectionReauditValidationIssue(
                    code="survey_correction_reaudit_target_type_out_of_scope",
                    finding_id=finding.id,
                    message=(
                        "Targeted re-audit v0.1 accepts only observation/relation findings; "
                        "survey/photo-level expansion requires a fresh independent audit."
                    ),
                )
            )

        for evidence in finding.photo_evidence:
            if evidence.photo_index not in known_candidate_photos:
                issues.append(
                    SurveyCorrectionReauditValidationIssue(
                        code="survey_correction_reaudit_unknown_photo",
                        finding_id=finding.id,
                        message=f"Unknown candidate photo {evidence.photo_index}.",
                    )
                )
            elif evidence.photo_index not in allowed_photos:
                issues.append(
                    SurveyCorrectionReauditValidationIssue(
                        code="survey_correction_reaudit_photo_out_of_scope",
                        finding_id=finding.id,
                        message=(
                            f"Photo {evidence.photo_index} is outside the deterministic "
                            "post-correction re-audit scope."
                        ),
                    )
                )

    return issues
