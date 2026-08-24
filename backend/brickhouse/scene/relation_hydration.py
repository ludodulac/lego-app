"""Deterministically preserve certain Survey relations in external Scene payloads.

The Survey is the semantic source of truth. External AI output may omit a relation
while still emitting both related objects. At the survey-aware API boundary we can
safely restore that already-proven relation without inventing new semantics.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from brickhouse.survey import ArchitecturalSurvey, Certainty, RelationKind

from .topology import ArchitecturalScene


def _payload_object_ids(scene_payload: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("volumes", "openings", "roofs", "chimneys", "platforms", "stairs", "equipment"):
        for item in scene_payload.get(key, []) or []:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                ids.add(item["id"])
            if key == "platforms" and isinstance(item, dict):
                for support in item.get("supports", []) or []:
                    if isinstance(support, dict) and isinstance(support.get("id"), str):
                        ids.add(support["id"])
    return ids


def hydrate_certain_survey_relations(
    survey: ArchitecturalSurvey,
    scene_payload: dict[str, Any],
) -> dict[str, Any]:
    """Restore omitted certain relations when both referenced Scene objects exist.

    Restored relations start as ``unresolved``. This is conservative: semantic
    continuity is known from the Survey, but metric contact must be proven separately.
    """
    payload = deepcopy(scene_payload)
    relations = list(payload.get("relations") or [])
    existing_ids = {
        item.get("id") for item in relations if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    object_ids = _payload_object_ids(payload)

    for relation in survey.relations:
        if relation.certainty is not Certainty.CERTAIN or relation.id in existing_ids:
            continue
        if relation.subject_id not in object_ids or relation.object_id not in object_ids:
            continue
        relations.append(
            {
                "id": relation.id,
                "kind": relation.kind.value,
                "subject_id": relation.subject_id,
                "object_id": relation.object_id,
                "certainty": relation.certainty.value,
                "geometry_status": "unresolved",
                "statement": relation.statement,
                "evidence": [
                    {
                        "photo_index": evidence.photo_index,
                        "observation": evidence.observation,
                    }
                    for evidence in relation.evidence
                ],
            }
        )
        existing_ids.add(relation.id)

    payload["relations"] = relations
    return payload


def _connection_is_metric(scene: ArchitecturalScene, subject_id: str, object_id: str) -> bool:
    volumes = {item.id: item for item in scene.volumes}
    platforms = {item.id: item for item in scene.platforms}
    stairs = {item.id: item for item in scene.stairs}

    a, b = subject_id, object_id
    if a in platforms and b in volumes:
        return scene._platform_touches_volume(platforms[a], volumes[b])
    if b in platforms and a in volumes:
        return scene._platform_touches_volume(platforms[b], volumes[a])
    if a in stairs and b in platforms:
        stair, platform = stairs[a], platforms[b]
        return scene._point_on_platform(stair.start, platform) or scene._point_on_platform(stair.end, platform)
    if b in stairs and a in platforms:
        stair, platform = stairs[b], platforms[a]
        return scene._point_on_platform(stair.start, platform) or scene._point_on_platform(stair.end, platform)
    if a in stairs and b in volumes:
        stair, volume = stairs[a], volumes[b]
        return scene._point_on_volume_boundary(stair.start, volume) or scene._point_on_volume_boundary(stair.end, volume)
    if b in stairs and a in volumes:
        stair, volume = stairs[b], volumes[a]
        return scene._point_on_volume_boundary(stair.start, volume) or scene._point_on_volume_boundary(stair.end, volume)
    return False


def resolve_proven_metric_connections(scene: ArchitecturalScene) -> ArchitecturalScene:
    """Promote only geometrically demonstrated unresolved ``connects_to`` relations."""
    updated = []
    changed = False
    for relation in scene.relations:
        if (
            relation.kind is RelationKind.CONNECTS_TO
            and relation.geometry_status == "unresolved"
            and _connection_is_metric(scene, relation.subject_id, relation.object_id)
        ):
            updated.append(relation.model_copy(update={"geometry_status": "resolved"}))
            changed = True
        else:
            updated.append(relation)
    if not changed:
        return scene
    return scene.model_copy(update={"relations": updated})
