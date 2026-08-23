"""Guard Scene exterior primitives against invention after the validated Survey.

The Survey is intentionally segmented before metric reconstruction. A Scene may
estimate coordinates for a plausible observed platform/stair, but it must not
manufacture a new landing or hidden stair run merely to make a circulation chain
look complete.
"""
from __future__ import annotations

from brickhouse.survey import ArchitecturalSurvey, Certainty, ObservationKind

from .models import ArchitecturalScene
from .survey_validation import (
    SceneSurveyIssue,
    SceneSurveySeverity,
    validate_scene_against_survey as _validate_scene_against_survey,
)

MAX_PLAUSIBLE_METRIC_CONFIDENCE = 0.65


def _guard_kind(
    survey: ArchitecturalSurvey,
    scene_objects,
    kind: ObservationKind,
) -> list[SceneSurveyIssue]:
    issues: list[SceneSurveyIssue] = []
    observations = {
        observation.id: observation
        for observation in survey.observations
        if observation.kind is kind
    }
    label = "plateforme" if kind is ObservationKind.PLATFORM else "volée d’escalier"

    for obj in scene_objects:
        observation = observations.get(obj.id)
        if observation is None:
            issues.append(
                SceneSurveyIssue(
                    code=f"scene_{kind.value}_not_in_survey",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=obj.id,
                    message=(
                        f"La {label} {obj.id!r} n’existe pas comme observation {kind.value!r} "
                        "dans le Survey validé. La Scene ne peut pas inventer une primitive cachée "
                        "pour compléter une circulation ; segmentez-la d’abord dans le Survey si une preuve existe."
                    ),
                )
            )
            continue
        if observation.certainty is Certainty.UNPROVEN:
            issues.append(
                SceneSurveyIssue(
                    code=f"unproven_{kind.value}_promoted",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=obj.id,
                    message=(
                        f"La {label} {obj.id!r} était `unproven` dans le Survey et ne peut pas devenir "
                        "une géométrie LEGO simplement parce qu’elle rendrait la topologie plus commode."
                    ),
                )
            )
            continue
        if (
            observation.certainty is Certainty.PLAUSIBLE
            and obj.source.confidence > MAX_PLAUSIBLE_METRIC_CONFIDENCE
        ):
            issues.append(
                SceneSurveyIssue(
                    code=f"plausible_{kind.value}_overconfidence",
                    severity=SceneSurveySeverity.WARNING,
                    object_id=obj.id,
                    message=(
                        f"La {label} {obj.id!r} reste seulement plausible dans le Survey, mais la Scene lui "
                        f"attribue une confiance métrique de {obj.source.confidence:.2f}. Tant qu’aucune nouvelle "
                        f"preuve ne la raffine, conservez une confiance ≤ {MAX_PLAUSIBLE_METRIC_CONFIDENCE:.2f}."
                    ),
                )
            )
    return issues


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Run the historical validator plus strict no-invention exterior guards."""
    issues = list(_validate_scene_against_survey(survey, scene))
    issues.extend(_guard_kind(survey, scene.platforms, ObservationKind.PLATFORM))
    issues.extend(_guard_kind(survey, scene.stairs, ObservationKind.STAIR))
    return issues
