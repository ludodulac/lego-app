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


def _building_boundary_ids(survey: ArchitecturalSurvey) -> set[str]:
    return {
        observation.id
        for observation in survey.observations
        if observation.kind is ObservationKind.BUILDING_BOUNDARY
    }


def _endpoint_matches(
    survey_id: str,
    scene_id: str,
    *,
    building_boundary_ids: set[str],
    scene_relation,
) -> bool:
    """Match one endpoint, allowing only the explicit anchored boundary alias.

    A Survey keeps facade-specific semantic boundary observations such as
    ``obs-building-boundary-left``. ArchitecturalScene deliberately does not render
    those observations as primitives; external reconstruction may therefore serialize
    the absent endpoint as the reserved token ``building_boundary`` and point
    ``semantic_anchor_volume_id`` at the concrete Scene volume. This is an identity
    bridge, not permission to rename arbitrary Survey objects.
    """
    if scene_id == survey_id:
        return True
    return (
        survey_id in building_boundary_ids
        and scene_id == "building_boundary"
        and scene_relation.semantic_anchor_volume_id is not None
    )


def _relation_endpoints_match(
    survey_relation,
    scene_relation,
    *,
    building_boundary_ids: set[str] | None = None,
) -> bool:
    """Compare relation endpoints according to relation semantics and boundary bridging.

    ``connects_to``, ``adjacent_to``, ``aligned_with`` and ``same_physical_object``
    describe undirected facts. ``supports`` and ``part_of`` remain directional.
    Facade-specific Survey ``building_boundary`` observations may additionally be
    represented by the reserved Scene alias ``building_boundary`` only when the
    relation supplies a concrete ``semantic_anchor_volume_id``.
    """
    boundaries = building_boundary_ids or set()

    def ordered_match(first_survey: str, second_survey: str) -> bool:
        return _endpoint_matches(
            first_survey,
            scene_relation.subject_id,
            building_boundary_ids=boundaries,
            scene_relation=scene_relation,
        ) and _endpoint_matches(
            second_survey,
            scene_relation.object_id,
            building_boundary_ids=boundaries,
            scene_relation=scene_relation,
        )

    if ordered_match(survey_relation.subject_id, survey_relation.object_id):
        return True
    if survey_relation.kind.value not in SYMMETRIC_RELATION_KINDS:
        return False
    return ordered_match(survey_relation.object_id, survey_relation.subject_id)


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
    boundary_ids = _building_boundary_ids(survey)
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
            or not _relation_endpoints_match(
                relation,
                candidate,
                building_boundary_ids=boundary_ids,
            )
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
