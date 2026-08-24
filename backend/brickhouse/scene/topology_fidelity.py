"""Fidelity checks for Survey relations preserved independently of metric geometry."""
from __future__ import annotations

from brickhouse.survey import ArchitecturalSurvey, Certainty

from .opening_visual_fidelity import validate_scene_against_survey as _validate_existing
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity
from .topology import ArchitecturalScene


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
            or candidate.subject_id != relation.subject_id
            or candidate.object_id != relation.object_id
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
    for issue in existing:
        if (
            issue.code == "certain_connection_broken"
            and issue.object_id in unresolved_connection_subjects
        ):
            continue
        issues.append(issue)
    return issues
