"""Guard Scene exterior primitives against invention after the validated Survey.

The Survey is intentionally segmented before metric reconstruction. A Scene may
estimate coordinates for a plausible observed platform/stair/grade, but it must
not manufacture hidden circulation or terrain merely to make a clean model.
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


def _confidence_issues(label: str, code_prefix: str, object_id: str, certainty, source):
    issues: list[SceneSurveyIssue] = []
    if source.kind.value == "generated_default":
        issues.append(
            SceneSurveyIssue(
                code=f"{code_prefix}_generated_default_geometry",
                severity=SceneSurveySeverity.ERROR,
                object_id=object_id,
                message=(
                    f"La géométrie de {label} {object_id!r} utilise `generated_default`. Une géométrie extérieure "
                    "doit être métriquement inférée depuis des preuves ou fournie par l’utilisateur, jamais créée par défaut."
                ),
            )
        )
    if certainty is Certainty.PLAUSIBLE and source.confidence > MAX_PLAUSIBLE_METRIC_CONFIDENCE:
        issues.append(
            SceneSurveyIssue(
                code=f"plausible_{code_prefix}_overconfidence",
                severity=SceneSurveySeverity.ERROR,
                object_id=object_id,
                message=(
                    f"{label.capitalize()} {object_id!r} reste seulement plausible dans le Survey, mais la Scene lui "
                    f"attribue une confiance métrique de {source.confidence:.2f}. Tant qu’aucune nouvelle preuve "
                    f"ne la raffine, conservez une confiance ≤ {MAX_PLAUSIBLE_METRIC_CONFIDENCE:.2f}."
                ),
            )
        )
    return issues


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
        issues.extend(_confidence_issues(label, kind.value, obj.id, observation.certainty, obj.source))
    return issues


def _guard_terrain(survey: ArchitecturalSurvey, scene: ArchitecturalScene) -> list[SceneSurveyIssue]:
    if scene.terrain is None:
        return []
    issues: list[SceneSurveyIssue] = []
    rank = {Certainty.UNPROVEN: 0, Certainty.PLAUSIBLE: 1, Certainty.CERTAIN: 2}
    for profile in scene.terrain.profiles:
        candidates = [
            observation
            for observation in survey.observations
            if observation.kind is ObservationKind.TERRAIN
            and observation.facade is profile.facade
            and observation.attributes.get("slope_direction")
        ]
        object_id = f"terrain:{profile.facade.value}"
        if not candidates:
            issues.append(
                SceneSurveyIssue(
                    code="scene_grade_not_in_survey",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=object_id,
                    message=(
                        f"La Scene crée un profil de pente sur {profile.facade.value!r}, mais le Survey validé "
                        "ne contient aucune observation de terrain indiquant une pente sur cette façade."
                    ),
                )
            )
            continue
        observation = max(candidates, key=lambda item: rank[item.certainty])
        if observation.certainty is Certainty.UNPROVEN:
            issues.append(
                SceneSurveyIssue(
                    code="unproven_grade_promoted",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=object_id,
                    message=(
                        f"La pente sur {profile.facade.value!r} reste `unproven` dans le Survey et ne peut pas "
                        "devenir un terrain métrique par défaut."
                    ),
                )
            )
            continue
        issues.extend(_confidence_issues("pente de terrain", "grade", object_id, observation.certainty, profile.source))
    return issues


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Run the historical validator plus strict no-invention exterior guards."""
    issues = list(_validate_scene_against_survey(survey, scene))
    issues.extend(_guard_kind(survey, scene.platforms, ObservationKind.PLATFORM))
    issues.extend(_guard_kind(survey, scene.stairs, ObservationKind.STAIR))
    issues.extend(_guard_terrain(survey, scene))
    return issues
