"""Independent visual audit contract for ArchitecturalSurvey.

SurveyAudit is intentionally diagnostic-only. It never mutates the Survey it
checks; a future explicit correction workflow may consume validated findings.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .models import ArchitecturalSurvey, PhotoEvidence


class SurveyAuditStatus(str, Enum):
    PASS = "pass"
    NEEDS_CORRECTION = "needs_correction"


class SurveyAuditFindingStatus(str, Enum):
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    MISSING = "missing"
    DUPLICATE = "duplicate"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    CONTRADICTION = "contradiction"


class SurveyAuditTargetType(str, Enum):
    OBSERVATION = "observation"
    RELATION = "relation"
    PHOTO = "photo"
    SURVEY = "survey"


class SurveyAuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SurveyAuditSuggestedAction(str, Enum):
    KEEP = "keep"
    LOWER_CERTAINTY = "lower_certainty"
    MERGE = "merge"
    ADD = "add"
    REMOVE = "remove"
    REORIENT = "reorient"
    REVIEW = "review"


class SurveyAuditSummary(BaseModel):
    status: SurveyAuditStatus
    issue_count: int = Field(ge=0)


class SurveyAuditFinding(BaseModel):
    id: str = Field(min_length=1)
    status: SurveyAuditFindingStatus
    target_type: SurveyAuditTargetType
    target_id: str | None = None
    severity: SurveyAuditSeverity
    photo_evidence: list[PhotoEvidence] = Field(default_factory=list)
    message: str = Field(min_length=1)
    suggested_action: SurveyAuditSuggestedAction

    @model_validator(mode="after")
    def validate_evidence_rule(self) -> "SurveyAuditFinding":
        if (
            self.status is not SurveyAuditFindingStatus.INSUFFICIENT_EVIDENCE
            and not self.photo_evidence
        ):
            raise ValueError(
                "survey audit findings must cite photo_evidence unless status is insufficient_evidence"
            )
        return self


class SurveyAudit(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    kind: Literal["survey_audit"] = "survey_audit"
    survey_id: str = Field(min_length=1)
    summary: SurveyAuditSummary
    findings: list[SurveyAuditFinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_summary_count(self) -> "SurveyAudit":
        if self.summary.issue_count != len(self.findings):
            raise ValueError("summary.issue_count must equal the number of findings")
        return self


@dataclass(frozen=True)
class SurveyAuditValidationIssue:
    code: str
    finding_id: str | None
    message: str
    severity: str = "error"


def validate_survey_audit(
    survey: ArchitecturalSurvey,
    audit: SurveyAudit,
) -> list[SurveyAuditValidationIssue]:
    """Validate that an independent audit only references claims it can check."""
    issues: list[SurveyAuditValidationIssue] = []

    if audit.survey_id != survey.id:
        issues.append(
            SurveyAuditValidationIssue(
                code="survey_audit_survey_id_mismatch",
                finding_id=None,
                message="SurveyAudit.survey_id must match the audited ArchitecturalSurvey.id.",
            )
        )

    known_photos = {photo.photo_index for photo in survey.photos}
    known_observations = {item.id for item in survey.observations}
    known_relations = {item.id for item in survey.relations}
    finding_ids: set[str] = set()

    for finding in audit.findings:
        if finding.id in finding_ids:
            issues.append(
                SurveyAuditValidationIssue(
                    code="survey_audit_duplicate_finding_id",
                    finding_id=finding.id,
                    message=f"Duplicate SurveyAudit finding id {finding.id!r}.",
                )
            )
        finding_ids.add(finding.id)

        for evidence in finding.photo_evidence:
            if evidence.photo_index not in known_photos:
                issues.append(
                    SurveyAuditValidationIssue(
                        code="survey_audit_unknown_photo",
                        finding_id=finding.id,
                        message=(
                            f"Finding {finding.id!r} references unknown photo "
                            f"{evidence.photo_index}."
                        ),
                    )
                )

        if finding.target_type is SurveyAuditTargetType.OBSERVATION:
            if not finding.target_id:
                issues.append(
                    SurveyAuditValidationIssue(
                        code="survey_audit_missing_observation_target",
                        finding_id=finding.id,
                        message="Observation findings require target_id.",
                    )
                )
            elif finding.target_id not in known_observations:
                issues.append(
                    SurveyAuditValidationIssue(
                        code="survey_audit_unknown_observation",
                        finding_id=finding.id,
                        message=f"Unknown Survey observation {finding.target_id!r}.",
                    )
                )
        elif finding.target_type is SurveyAuditTargetType.RELATION:
            if not finding.target_id:
                issues.append(
                    SurveyAuditValidationIssue(
                        code="survey_audit_missing_relation_target",
                        finding_id=finding.id,
                        message="Relation findings require target_id.",
                    )
                )
            elif finding.target_id not in known_relations:
                issues.append(
                    SurveyAuditValidationIssue(
                        code="survey_audit_unknown_relation",
                        finding_id=finding.id,
                        message=f"Unknown Survey relation {finding.target_id!r}.",
                    )
                )
        elif finding.target_type is SurveyAuditTargetType.PHOTO:
            if not finding.target_id:
                issues.append(
                    SurveyAuditValidationIssue(
                        code="survey_audit_missing_photo_target",
                        finding_id=finding.id,
                        message="Photo findings require target_id containing the photo_index.",
                    )
                )
            else:
                try:
                    target_photo_index = int(finding.target_id)
                except ValueError:
                    target_photo_index = -1
                if target_photo_index not in known_photos:
                    issues.append(
                        SurveyAuditValidationIssue(
                            code="survey_audit_unknown_photo_target",
                            finding_id=finding.id,
                            message=f"Unknown Survey photo target {finding.target_id!r}.",
                        )
                    )

    actionable = any(
        finding.suggested_action is not SurveyAuditSuggestedAction.KEEP
        and finding.severity in {SurveyAuditSeverity.WARNING, SurveyAuditSeverity.ERROR}
        for finding in audit.findings
    )
    expected_status = (
        SurveyAuditStatus.NEEDS_CORRECTION if actionable else SurveyAuditStatus.PASS
    )
    if audit.summary.status is not expected_status:
        issues.append(
            SurveyAuditValidationIssue(
                code="survey_audit_summary_status_mismatch",
                finding_id=None,
                message=(
                    f"SurveyAudit summary status must be {expected_status.value!r} for "
                    "the current actionable findings."
                ),
            )
        )

    return issues
