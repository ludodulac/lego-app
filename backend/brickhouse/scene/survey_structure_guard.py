"""Guard ArchitecturalScene against unsupported promotion of Survey hypotheses.

The Survey is segmented before metric reconstruction. A Scene may estimate metric
coordinates for supported observations, but it must not manufacture hidden
circulation, terrain or rearrange the qualitative opening layout merely to make a
clean model.
"""
from __future__ import annotations

from itertools import combinations

from brickhouse.survey import ArchitecturalSurvey, Certainty, ObservationKind

from .models import ArchitecturalScene
from .survey_validation import (
    SceneSurveyIssue,
    SceneSurveySeverity,
    validate_scene_against_survey as _validate_scene_against_survey,
)

MAX_PLAUSIBLE_METRIC_CONFIDENCE = 0.65


def _superseded_observation_ids(survey: ArchitecturalSurvey) -> set[str]:
    """Observation ids replaced by an append-only refinement later in the Survey."""
    return {
        target_id
        for observation in survey.observations
        if isinstance((target_id := observation.attributes.get("refines_observation_id")), str)
        and target_id
    }


def _positive_rank(value):
    """Accept only explicit positive integer qualitative ranks; ignore legacy/free text."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


def _opening_host_key(observation) -> str:
    host = observation.attributes.get("host_object")
    return host if isinstance(host, str) and host else "__primary__"


def _guard_opening_layout(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Keep certain qualitative left/right and low/high relationships before metrics.

    Survey ranks are intentionally ordinal, not dimensional. Distinct ranks must
    retain their order; equal ranks merely mean the Survey did not distinguish the
    objects along that axis and do not force exact alignment.
    """
    issues: list[SceneSurveyIssue] = []
    superseded = _superseded_observation_ids(survey)
    scene_openings = {opening.id: opening for opening in scene.openings}
    observations = [
        observation
        for observation in survey.observations
        if observation.kind is ObservationKind.OPENING
        and observation.certainty is Certainty.CERTAIN
        and observation.id not in superseded
        and observation.id in scene_openings
    ]

    for first, second in combinations(observations, 2):
        if first.facade is None or first.facade is not second.facade:
            continue
        if _opening_host_key(first) != _opening_host_key(second):
            continue
        a = scene_openings[first.id]
        b = scene_openings[second.id]
        if a.volume_id != b.volume_id:
            continue

        first_h = _positive_rank(first.attributes.get("facade_horizontal_rank"))
        second_h = _positive_rank(second.attributes.get("facade_horizontal_rank"))
        if first_h is not None and second_h is not None and first_h != second_h:
            a_center = a.offset_horizontal + a.width / 2
            b_center = b.offset_horizontal + b.width / 2
            expected = a_center < b_center if first_h < second_h else a_center > b_center
            if not expected:
                issues.append(
                    SceneSurveyIssue(
                        code="opening_horizontal_order_drift",
                        severity=SceneSurveySeverity.ERROR,
                        object_id=first.id,
                        message=(
                            f"Les ouvertures {first.id!r} et {second.id!r} ont inversé leur ordre horizontal sur "
                            f"la façade {first.facade.value!r}. Le Survey impose les rangs {first_h} et {second_h}; "
                            "la métrique ne peut pas modifier cette relation qualitative."
                        ),
                    )
                )

        first_v = _positive_rank(first.attributes.get("facade_vertical_rank"))
        second_v = _positive_rank(second.attributes.get("facade_vertical_rank"))
        if first_v is not None and second_v is not None and first_v != second_v:
            a_center = a.offset_vertical + a.height / 2
            b_center = b.offset_vertical + b.height / 2
            expected = a_center < b_center if first_v < second_v else a_center > b_center
            if not expected:
                issues.append(
                    SceneSurveyIssue(
                        code="opening_vertical_order_drift",
                        severity=SceneSurveySeverity.ERROR,
                        object_id=first.id,
                        message=(
                            f"Les ouvertures {first.id!r} et {second.id!r} ont inversé leur ordre vertical sur "
                            f"la façade {first.facade.value!r}. Le Survey impose les rangs {first_v} et {second_v}; "
                            "la métrique ne peut pas modifier cette relation qualitative."
                        ),
                    )
                )
    return issues


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
    superseded = _superseded_observation_ids(survey)
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
        if obj.id in superseded:
            issues.append(
                SceneSurveyIssue(
                    code=f"superseded_{kind.value}_rendered",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=obj.id,
                    message=(
                        f"La {label} {obj.id!r} a été raffinée par une observation plus récente du Survey. "
                        "Elle doit rester une provenance historique et ne peut pas être rendue comme un deuxième objet physique."
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
    superseded = _superseded_observation_ids(survey)
    rank = {Certainty.UNPROVEN: 0, Certainty.PLAUSIBLE: 1, Certainty.CERTAIN: 2}
    for profile in scene.terrain.profiles:
        candidates = [
            observation
            for observation in survey.observations
            if observation.kind is ObservationKind.TERRAIN
            and observation.id not in superseded
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
                        "ne contient aucune observation active de terrain indiquant une pente sur cette façade."
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
    """Run historical validation plus strict no-invention/order guards."""
    issues = list(_validate_scene_against_survey(survey, scene))
    issues.extend(_guard_opening_layout(survey, scene))
    issues.extend(_guard_kind(survey, scene.platforms, ObservationKind.PLATFORM))
    issues.extend(_guard_kind(survey, scene.stairs, ObservationKind.STAIR))
    issues.extend(_guard_terrain(survey, scene))
    return issues
