import json
from pathlib import Path

import pytest

from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


REFERENCE = Path("tests/fixtures/bh233-reference-scene.json")


def test_bh233_frozen_reference_scene_reaches_first_real_brick_model():
    raw = REFERENCE.read_text(encoding="utf-8")
    scene = ArchitecturalScene.model_validate_json(raw)

    relation = next(item for item in scene.relations if item.id == "relation-stair-platform")
    assert relation.kind.value == "connects_to"
    assert relation.subject_id == "stair-exterior-1"
    assert relation.object_id == "platform-massive-1"
    assert relation.certainty.value == "certain"
    assert relation.geometry_status == "resolved"

    bundle = run_m0_pipeline_scene(scene, front_width_studs=48)
    parts = bundle.brick_model.parts

    prefixes = {
        "platform_timber": "scene-platform:platform-timber-1:",
        "platform_massive": "scene-platform:platform-massive-1:",
        "stair": "scene-stair:stair-exterior-1:",
    }
    critical = {}
    for name, prefix in prefixes.items():
        selected = [part for part in parts if part.placement_id.startswith(prefix)]
        critical[name] = {
            "count": len(selected),
            "x": [min((p.x_studs for p in selected), default=None), max((p.x_studs for p in selected), default=None)],
            "y": [min((p.y_studs for p in selected), default=None), max((p.y_studs for p in selected), default=None)],
            "z": [min((p.z_plates for p in selected), default=None), max((p.z_plates for p in selected), default=None)],
            "categories": sorted({p.category for p in selected}),
        }

    relevant_ids = {"platform-timber-1", "platform-massive-1", "stair-exterior-1", "volume-exterior-1"}
    issues = [
        {
            "code": issue.code,
            "severity": issue.severity,
            "object_id": issue.object_id,
            "message": issue.message,
        }
        for issue in bundle.fidelity_issues
        if issue.object_id in relevant_ids or "platform" in issue.code or "stair" in issue.code
    ]

    summary = {
        "architectural_scene_parsed": True,
        "parsed_relation_ids": [item.id for item in scene.relations],
        "parsed_platform_ids": [item.id for item in scene.platforms],
        "parsed_stair_ids": [item.id for item in scene.stairs],
        "parsed_has_platform_structure_observations_field": hasattr(scene, "platform_structure_observations"),
        "brick_model_produced": True,
        "total_parts": len(parts),
        "model_bounds": {
            "width_studs": bundle.brick_model.width_studs,
            "depth_studs": bundle.brick_model.depth_studs,
            "height_plates": bundle.brick_model.height_plates,
        },
        "critical": critical,
        "relevant_fidelity_issues": issues,
    }
    pytest.fail("BH233_REFERENCE_OBSERVATION=" + json.dumps(summary, sort_keys=True))
