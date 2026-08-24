"""Projection wrapper that blocks LEGO only for certain unresolved topology."""
from __future__ import annotations

from brickhouse.survey import Certainty

from .projection import (
    ProjectionIssue,
    ProjectionResult,
    ProjectionSeverity,
    project_scene_to_building as _project_metric_scene,
)
from .topology import ArchitecturalScene


def project_scene_to_building(scene: ArchitecturalScene) -> ProjectionResult:
    result = _project_metric_scene(scene)
    unresolved = [
        relation
        for relation in scene.relations
        if relation.geometry_status == "unresolved"
    ]
    if not unresolved:
        return result

    issues = [*result.issues]
    blockers = []
    for relation in unresolved:
        if relation.certainty is Certainty.CERTAIN:
            severity = ProjectionSeverity.BLOCKER
            blockers.append(relation)
            message = (
                f"La relation architecturale {relation.id!r} est certaine mais son raccord métrique "
                "n'est pas encore résolu. La projection LEGO est bloquée plutôt que d'inventer la jonction."
            )
        else:
            severity = ProjectionSeverity.WARNING
            message = (
                f"La relation architecturale {relation.id!r} reste {relation.certainty.value} et son raccord "
                "métrique n'est pas résolu. Elle est conservée dans ArchitecturalScene sans bloquer à elle seule "
                "la projection LEGO."
            )
        issues.append(
            ProjectionIssue(
                code="topological_relation_geometry_unresolved",
                severity=severity,
                object_id=relation.id,
                message=message,
            )
        )

    if not blockers:
        return result.model_copy(update={"issues": issues})
    return result.model_copy(update={"building": None, "issues": issues})
