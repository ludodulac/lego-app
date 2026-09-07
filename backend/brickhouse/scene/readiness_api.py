"""Shared strict Scene readiness evaluation for validation and build boundaries."""
from __future__ import annotations

from brickhouse.bricks.scene_architecture import _validate_exterior_primitives
from brickhouse.pipeline_probe import _required_inputs_for_projection
from brickhouse.vision.compatibility import assess_m0_compatibility

from .models import ArchitecturalScene, ProjectionIssue, ProjectionSeverity
from .readiness import ArchitecturalReadinessReport, assess_architectural_readiness
from .topology_projection import project_scene_to_building


def evaluate_strict_scene_readiness(scene: ArchitecturalScene):
    """Compute projection plus the single backend decision strict builders must use."""
    projection = project_scene_to_building(scene)
    if not projection.blocked:
        try:
            _validate_exterior_primitives(scene)
        except ValueError as exc:
            projection = projection.model_copy(
                update={
                    "issues": [
                        *projection.issues,
                        ProjectionIssue(
                            code="scene_architecture_not_buildable",
                            severity=ProjectionSeverity.BLOCKER,
                            message=str(exc),
                        ),
                    ]
                }
            )
    required_inputs = _required_inputs_for_projection(scene, projection)
    compatibility = (
        assess_m0_compatibility(projection.building)
        if projection.building is not None
        else None
    )
    readiness: ArchitecturalReadinessReport = assess_architectural_readiness(
        scene,
        projection,
        required_inputs,
        compatibility,
    )
    return projection, required_inputs, compatibility, readiness
