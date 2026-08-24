"""Projection wrapper that blocks LEGO while topological junctions remain unresolved."""
from __future__ import annotations

from .projection import (
    ProjectionIssue,
    ProjectionResult,
    ProjectionSeverity,
    project_scene_to_building as _project_metric_scene,
)
from .topology import ArchitecturalScene


def project_scene_to_building(scene: ArchitecturalScene) -> ProjectionResult:
    result = _project_metric_scene(scene)
    unresolved = [relation for relation in scene.relations if relation.geometry_status == "unresolved"]
    if not unresolved:
        return result

    issues = [*result.issues]
    for relation in unresolved:
        issues.append(
            ProjectionIssue(
                code="topological_relation_geometry_unresolved",
                severity=ProjectionSeverity.BLOCKER,
                object_id=relation.id,
                message=(
                    f"La relation architecturale {relation.id!r} est comprise mais son raccord métrique "
                    "n'est pas encore résolu. La projection LEGO est bloquée plutôt que d'inventer la jonction."
                ),
            )
        )
    return result.model_copy(update={"building": None, "issues": issues})
