"""Architectural survey: photo observations before scene reconstruction."""

from .audit import (
    SurveyAudit,
    SurveyAuditFinding,
    SurveyAuditFindingStatus,
    SurveyAuditSeverity,
    SurveyAuditStatus,
    SurveyAuditSuggestedAction,
    SurveyAuditSummary,
    SurveyAuditTargetType,
    SurveyAuditValidationIssue,
    validate_survey_audit,
)
from .correction import (
    SurveyCorrection,
    SurveyCorrectionChange,
    SurveyCorrectionObjectType,
    SurveyCorrectionValidationIssue,
    validate_survey_correction,
)
from .models import (
    ArchitecturalSurvey,
    CanonicalFrame,
    Certainty,
    KnownMeasurement,
    NormalizedImageRegion,
    ObservationKind,
    OpeningVisualDescription,
    PhotoEvidence,
    PhotoView,
    RelationKind,
    RepresentationPolicy,
    SurfaceAppearance,
    SurveyObservation,
    SurveyRelation,
)
from .reasoning import (
    QuestionImpact,
    SurveyHypothesis,
    SurveyOpenQuestion,
    SurveyReasoningState,
    rank_questions_for_user_input,
)
from .roof_guard import validate_multiview_roof_hypotheses
from .validation import (
    SurveyValidationIssue,
    validate_survey_extension as _validate_survey_extension,
    validate_survey_semantics as _validate_survey_semantics,
)


def validate_survey_semantics(survey: ArchitecturalSurvey) -> list[SurveyValidationIssue]:
    """Run core Survey semantics plus targeted anti-loss guards."""
    return [
        *_validate_survey_semantics(survey),
        *validate_multiview_roof_hypotheses(survey),
    ]


def validate_survey_extension(
    base: ArchitecturalSurvey,
    candidate: ArchitecturalSurvey,
) -> list[SurveyValidationIssue]:
    """Run append-only extension validation plus targeted anti-loss guards."""
    issues = _validate_survey_extension(base, candidate)
    roof_issues = validate_multiview_roof_hypotheses(candidate)
    existing = {(issue.code, issue.observation_id) for issue in issues}
    issues.extend(
        issue
        for issue in roof_issues
        if (issue.code, issue.observation_id) not in existing
    )
    return issues


__all__ = [
    "ArchitecturalSurvey",
    "CanonicalFrame",
    "Certainty",
    "KnownMeasurement",
    "NormalizedImageRegion",
    "ObservationKind",
    "OpeningVisualDescription",
    "PhotoEvidence",
    "PhotoView",
    "QuestionImpact",
    "RelationKind",
    "RepresentationPolicy",
    "SurfaceAppearance",
    "SurveyAudit",
    "SurveyAuditFinding",
    "SurveyAuditFindingStatus",
    "SurveyAuditSeverity",
    "SurveyAuditStatus",
    "SurveyAuditSuggestedAction",
    "SurveyAuditSummary",
    "SurveyAuditTargetType",
    "SurveyAuditValidationIssue",
    "SurveyCorrection",
    "SurveyCorrectionChange",
    "SurveyCorrectionObjectType",
    "SurveyCorrectionValidationIssue",
    "SurveyHypothesis",
    "SurveyObservation",
    "SurveyOpenQuestion",
    "SurveyReasoningState",
    "SurveyRelation",
    "SurveyValidationIssue",
    "rank_questions_for_user_input",
    "validate_survey_audit",
    "validate_survey_correction",
    "validate_survey_extension",
    "validate_survey_semantics",
    "validate_multiview_roof_hypotheses",
]
