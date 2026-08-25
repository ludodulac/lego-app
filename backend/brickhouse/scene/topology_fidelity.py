"""Fidelity checks for Survey relations preserved independently of metric geometry."""
from __future__ import annotations

from collections import Counter

from brickhouse.survey import ArchitecturalSurvey, Certainty, ObservationKind

from .opening_visual_fidelity import validate_scene_against_survey as _validate_existing
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity
from .topology import ArchitecturalScene


SYMMETRIC_RELATION_KINDS = {
    "connects_to",
    "adjacent_to",
    "aligned_with",
    "same_physical_object",
}


def _facade_opening_counts_match_by_survey_identity(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> bool:
    """Compare facade counts without assuming every primary opening stays on volume[0].

    The historical count guard filters Survey openings by semantic ``host_object``
    but filters Scene openings by ``scene.volumes[0]``. In a legitimate multi-volume
    reconstruction, an opening can keep its exact Survey identity/facade while being
    assigned to a secondary Scene volume; counting only the first volume then creates
    a false ``facade_opening_count_drift``. Identity is the stable cross-layer key.
    """
    survey_openings = {
        observation.id: observation
        for observation in survey.observations
        if observation.kind is ObservationKind.OPENING
    }
    expected = Counter(
        observation.facade
        for observation in survey_openings.values()
        if observation.certainty is Certainty.CERTAIN
        and observation.facade is not None
        and not observation.attributes.get("host_object")
    )
    actual = Counter()
    for opening in scene.openings:
        observation = survey_openings.get(opening.id)
        if (
            observation is None
            or observation.certainty is not Certainty.CERTAIN
            or observation.facade is None
            or observation.attributes.get("host_object")
        ):
            continue
        actual[opening.facade] += 1
    return actual == expected


def _relation_endpoints_match(survey_relation, scene_relation) -> bool:
    """Compare relation endpoints according to the semantics of the relation kind.

    `connects_to`, `adjacent_to`, `aligned_with` and `same_physical_object` describe
    undirected facts: A connects to B is the same fact as B connects to A. External
    reconstruction models can legitimately serialize these endpoints in either order,
    especially when one endpoint is a semantic building boundary represented through
    `semantic_anchor_volume_id`. Direction remains strict for asymmetric relations
    such as `supports` and `part_of`.
    """
    exact = (
        scene_relation.subject_id == survey_relation.subject_id
        and scene_relation.object_id == survey_relation.object_id
    )
    if exact:
        return True
    if survey_relation.kind.value not in SYMMETRIC_RELATION_KINDS:
        return False
    return (
        scene_relation.subject_id == survey_relation.object_id
        and scene_relation.object_id == survey_relation.subject_id
    )


def validate_scene_against_survey(
    survey: ArchitecturalSurvey,
    scene: ArchitecturalScene,
) -> list[SceneSurveyIssue]:
    """Run existing fidelity checks, then enforce preservation of certain relations.

    A certain relation may remain metrically unresolved. In that case the Scene is a
    faithful understanding artifact, but projection will remain blocked until the
    geometric junction is resolved.
    """
    scene_relations = {relation.id: relation for relation in scene.relations}
    unresolved_connection_subjects: set[str] = set()
    issues: list[SceneSurveyIssue] = []

    for relation in survey.relations:
        if relation.certainty is not Certainty.CERTAIN:
            continue
        candidate = scene_relations.get(relation.id)
        if candidate is None:
            issues.append(
                SceneSurveyIssue(
                    code="certain_relation_missing",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=relation.subject_id,
                    message=f"La relation certaine {relation.id!r} a disparu de la Scene.",
                )
            )
            continue
        if (
            candidate.kind is not relation.kind
            or not _relation_endpoints_match(relation, candidate)
            or candidate.certainty is not Certainty.CERTAIN
        ):
            issues.append(
                SceneSurveyIssue(
                    code="certain_relation_drift",
                    severity=SceneSurveySeverity.ERROR,
                    object_id=relation.subject_id,
                    message=f"La relation certaine {relation.id!r} a changé de sens, de type ou de certitude.",
                )
            )
            continue
        if relation.kind.value == "connects_to" and candidate.geometry_status == "unresolved":
            unresolved_connection_subjects.add(relation.subject_id)
            unresolved_connection_subjects.add(relation.object_id)
            issues.append(
                SceneSurveyIssue(
                    code="certain_connection_metric_unresolved",
                    severity=SceneSurveySeverity.WARNING,
                    object_id=relation.subject_id,
                    message=(
                        f"La relation certaine {relation.id!r} est conservée topologiquement, mais son raccord "
                        "métrique reste inconnu. La Scene reste fidèle; la projection LEGO doit rester bloquée."
                    ),
                )
            )

    existing = list(_validate_existing(survey, scene))
    counts_match_by_identity = _facade_opening_counts_match_by_survey_identity(survey, scene)
    for issue in existing:
        if (
            issue.code == "certain_connection_broken"
            and issue.object_id in unresolved_connection_subjects
        ):
            continue
        if issue.code == "facade_opening_count_drift" and counts_match_by_identity:
            continue
        issues.append(issue)
    return issues
