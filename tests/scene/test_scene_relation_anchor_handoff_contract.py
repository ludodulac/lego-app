from pathlib import Path

import pytest
from pydantic import ValidationError

from brickhouse.scene import ArchitecturalScene

SOURCE = {"kind": "inferred", "confidence": 0.5}


def _payload() -> dict:
    return {
        "schema_version": "0.2",
        "id": "scene-relation-anchor-contract",
        "name": "relation anchor contract",
        "units": "m",
        "volumes": [
            {
                "id": "volume_main",
                "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "width": {"value": 10.0, "source": SOURCE},
                "depth": {"value": 10.0, "source": SOURCE},
                "height": {"value": 6.0, "source": SOURCE},
                "floors": 2,
                "source": SOURCE,
            },
            {
                "id": "volume_attached",
                "position": {"x": -3.0, "y": 3.0, "z": 0.0},
                "width": {"value": 3.0, "source": SOURCE},
                "depth": {"value": 3.0, "source": SOURCE},
                "height": {"value": 3.0, "source": SOURCE},
                "floors": 1,
                "source": SOURCE,
            },
        ],
        "relations": [],
        "appearance": {},
    }


def _relation(*, object_id: str, geometry_status: str, anchor: str | None = None) -> dict:
    relation = {
        "id": "rel-attached",
        "kind": "connects_to",
        "subject_id": "volume_attached",
        "object_id": object_id,
        "certainty": "certain",
        "geometry_status": geometry_status,
        "statement": "Attached volume connects to the main building.",
        "evidence": [],
    }
    if anchor is not None:
        relation["semantic_anchor_volume_id"] = anchor
    return relation


def test_two_resolved_scene_endpoints_forbid_redundant_semantic_anchor() -> None:
    payload = _payload()
    payload["relations"] = [
        _relation(object_id="volume_main", geometry_status="resolved", anchor="volume_main")
    ]

    with pytest.raises(ValidationError, match="two Scene endpoints.*must not define semantic_anchor_volume_id"):
        ArchitecturalScene.model_validate(payload)


def test_semantic_non_materialized_endpoint_may_use_resolved_volume_anchor() -> None:
    payload = _payload()
    payload["relations"] = [
        _relation(object_id="building_boundary", geometry_status="resolved", anchor="volume_main")
    ]

    scene = ArchitecturalScene.model_validate(payload)
    relation = scene.relations[0]
    assert relation.object_id == "building_boundary"
    assert relation.semantic_anchor_volume_id == "volume_main"


def test_unresolved_relation_with_anchor_remains_forbidden() -> None:
    payload = _payload()
    payload["relations"] = [
        _relation(object_id="building_boundary", geometry_status="unresolved", anchor="volume_main")
    ]

    with pytest.raises(ValidationError, match="unresolved.*semantic_anchor_volume_id"):
        ArchitecturalScene.model_validate(payload)


def test_handoff_v48_states_existing_schema_without_weakening_it() -> None:
    contract = Path("frontend/scene-handoff-relation-anchor-v48.js").read_text(encoding="utf-8")
    assert "SCENE RELATION ANCHOR CONTRACT v4.8" in contract
    assert "if BOTH subject_id and object_id already identify concrete Scene primitives" in contract
    assert "OMIT semantic_anchor_volume_id" in contract
    assert "exactly one endpoint remains a semantic/non-materialized" in contract
    assert 'geometry_status:"unresolved"' in contract
