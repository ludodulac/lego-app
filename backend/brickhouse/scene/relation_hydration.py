"""Hydrate certain Survey relations before ArchitecturalScene validation.

The Survey is the semantic source of truth. External Scene JSON can omit a
relation while still emitting the referenced objects. Because ArchitecturalScene
validates exterior connectivity during model parsing, those already-proven
relations must be restored on the raw payload before parsing, not afterwards.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from brickhouse.survey import ArchitecturalSurvey, Certainty


def hydrate_certain_survey_relations(
    survey: ArchitecturalSurvey,
    scene_payload: dict[str, Any],
) -> dict[str, Any]:
    """Restore omitted certain Survey relations when both Scene objects exist.

    The restored relation is marked ``unresolved``: topology is proven by the
    Survey, but metric contact is not invented merely to satisfy connectivity.
    """
    payload = deepcopy(scene_payload)
    relations = list(payload.get("relations") or [])
    existing_ids = {
        item.get("id")
        for item in relations
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    object_ids: set[str] = set()
    for key in ("volumes", "openings", "roofs", "chimneys", "platforms", "stairs", "equipment"):
        for item in payload.get(key, []) or []:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                object_ids.add(item["id"])
            if key == "platforms" and isinstance(item, dict):
                for support in item.get("supports", []) or []:
                    if isinstance(support, dict) and isinstance(support.get("id"), str):
                        object_ids.add(support["id"])

    for relation in survey.relations:
        if relation.certainty is not Certainty.CERTAIN or relation.id in existing_ids:
            continue
        if relation.subject_id not in object_ids or relation.object_id not in object_ids:
            continue
        relations.append({
            "id": relation.id,
            "kind": relation.kind.value,
            "subject_id": relation.subject_id,
            "object_id": relation.object_id,
            "certainty": relation.certainty.value,
            "geometry_status": "unresolved",
            "statement": relation.statement,
            "evidence": [
                {"photo_index": evidence.photo_index, "observation": evidence.observation}
                for evidence in relation.evidence
            ],
        })
        existing_ids.add(relation.id)

    payload["relations"] = relations
    return payload
