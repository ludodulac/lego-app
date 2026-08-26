"""Prepare a conservative buildable subset of a partially resolved ArchitecturalScene.

This module never guesses missing geometry. It only omits scene objects whose own
construction geometry, or a required topological junction, is explicitly unresolved.
The original ArchitecturalScene remains authoritative and untouched.
"""
from __future__ import annotations

from dataclasses import dataclass

from brickhouse.scene.models import ArchitecturalScene, SceneRoofType


@dataclass(frozen=True)
class PartialSceneOmission:
    object_id: str
    reason: str


def _is_unresolved(value) -> bool:
    raw = getattr(value, "value", value)
    return raw == "unresolved"


def prepare_partial_build_scene(
    scene: ArchitecturalScene,
) -> tuple[ArchitecturalScene, list[PartialSceneOmission]]:
    """Return a scene containing only geometry safe to construct now.

    Rules are intentionally narrow:
    - incomplete gable/shed roofs are omitted instead of assigned a pitch/direction;
    - platforms/stairs involved in an explicitly unresolved metric junction are
      omitted until the junction is resolved;
    - relations referencing omitted objects are omitted from the temporary copy.

    Volumes and openings are preserved so the first trustworthy wall courses and
    known openings can already become real LEGO placements.
    """
    omissions: list[PartialSceneOmission] = []
    omitted_ids: set[str] = set()

    kept_roofs = []
    for roof in scene.roofs:
        incomplete = False
        if roof.type is SceneRoofType.GABLE:
            incomplete = roof.ridge_direction is None or roof.pitch_degrees is None
        elif roof.type is SceneRoofType.SHED:
            incomplete = roof.down_slope_direction is None or roof.pitch_degrees is None
        if incomplete:
            omitted_ids.add(roof.id)
            omissions.append(
                PartialSceneOmission(
                    object_id=roof.id,
                    reason="roof_geometry_unresolved",
                )
            )
        else:
            kept_roofs.append(roof)

    unresolved_relation_object_ids: set[str] = set()
    for relation in getattr(scene, "relations", []):
        if _is_unresolved(getattr(relation, "geometry_status", None)):
            unresolved_relation_object_ids.update(
                {relation.subject_id, relation.object_id}
            )

    kept_platforms = []
    for platform in scene.platforms:
        if platform.id in unresolved_relation_object_ids:
            omitted_ids.add(platform.id)
            omissions.append(
                PartialSceneOmission(
                    object_id=platform.id,
                    reason="required_junction_geometry_unresolved",
                )
            )
        else:
            kept_platforms.append(platform)

    kept_stairs = []
    for stair in scene.stairs:
        if stair.id in unresolved_relation_object_ids:
            omitted_ids.add(stair.id)
            omissions.append(
                PartialSceneOmission(
                    object_id=stair.id,
                    reason="required_junction_geometry_unresolved",
                )
            )
        else:
            kept_stairs.append(stair)

    updates = {
        "roofs": kept_roofs,
        "platforms": kept_platforms,
        "stairs": kept_stairs,
    }
    if hasattr(scene, "relations"):
        updates["relations"] = [
            relation
            for relation in scene.relations
            if relation.subject_id not in omitted_ids
            and relation.object_id not in omitted_ids
        ]

    return scene.model_copy(update=updates), omissions
