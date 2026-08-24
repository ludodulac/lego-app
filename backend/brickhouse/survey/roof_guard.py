"""Targeted semantic guard for roof information loss in multiview Surveys."""

from __future__ import annotations

from .models import ArchitecturalSurvey, ObservationKind
from .validation import SurveyValidationIssue

_ROOF_SHAPE_KEYS = (
    "roof_type",
    "facade_is_gable",
    "facade_roof_relationship",
    "roof_edge_type",
)


def validate_multiview_roof_hypotheses(
    survey: ArchitecturalSurvey,
) -> list[SurveyValidationIssue]:
    """Reject silent loss of all qualitative roof-shape information.

    This guard is deliberately non-metric. A roof observed in two or more photos
    does not need a pitch, ridge axis, height or dimensions. It does need at least
    one explicit qualitative shape/edge hypothesis when such a hypothesis has
    survived the Survey output, with uncertainty carried separately by
    ``attribute_certainty``.
    """
    issues: list[SurveyValidationIssue] = []
    for observation in survey.observations:
        if observation.kind is not ObservationKind.ROOF:
            continue
        distinct_photos = {item.photo_index for item in observation.evidence}
        if len(distinct_photos) < 2:
            continue
        if any(key in observation.attributes for key in _ROOF_SHAPE_KEYS):
            continue
        issues.append(
            SurveyValidationIssue(
                code="multiview_roof_missing_shape_hypothesis",
                observation_id=observation.id,
                message=(
                    "Une toiture recoupée dans plusieurs vues ne peut pas perdre toute "
                    "hypothèse qualitative de forme. Conservez roof_type, facade_is_gable, "
                    "facade_roof_relationship ou roof_edge_type avec sa certitude d’attribut; "
                    "n’inventez aucune métrique."
                ),
            )
        )
    return issues
