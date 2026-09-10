import json
from pathlib import Path

from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene.models import ArchitecturalScene


FIXTURE = Path(__file__).parents[1] / "fixtures" / "bh233-checkpoint-scene.json"
CRITICAL_IDS = ("platform-massive-1", "platform-timber-1", "stair-exterior-1")


def test_bh233_observe_exact_validated_scene_through_real_scene_pipeline():
    scene = ArchitecturalScene.model_validate_json(FIXTURE.read_text(encoding="utf-8"))
    bundle = run_m0_pipeline_scene(scene, front_width_studs=48)
    parts = bundle.brick_model.parts

    by_object = {
        object_id: [
            part for part in parts
            if part.placement_id.startswith(f"scene-platform:{object_id}:")
            or part.placement_id.startswith(f"scene-stair:{object_id}:")
        ]
        for object_id in CRITICAL_IDS
    }
    summary = {
        "total_parts": len(parts),
        "model_bounds": {
            "width_studs": bundle.brick_model.width_studs,
            "depth_studs": bundle.brick_model.depth_studs,
            "height_plates": bundle.brick_model.height_plates,
            "canvas_width_studs": bundle.brick_model.canvas_width_studs,
            "canvas_depth_studs": bundle.brick_model.canvas_depth_studs,
            "origin_x_studs": bundle.brick_model.origin_x_studs,
            "origin_y_studs": bundle.brick_model.origin_y_studs,
        },
        "critical": {
            object_id: {
                "part_count": len(object_parts),
                "x": [min((p.x_studs for p in object_parts), default=None), max((p.x_studs for p in object_parts), default=None)],
                "y": [min((p.y_studs for p in object_parts), default=None), max((p.y_studs for p in object_parts), default=None)],
                "z": [min((p.z_plates for p in object_parts), default=None), max((p.z_plates for p in object_parts), default=None)],
                "categories": sorted({p.category for p in object_parts}),
            }
            for object_id, object_parts in by_object.items()
        },
        "critical_fidelity_issues": [
            {
                "code": issue.code,
                "severity": issue.severity,
                "object_id": issue.object_id,
                "message": issue.message,
            }
            for issue in bundle.fidelity_issues
            if issue.object_id in CRITICAL_IDS
            or "platform" in issue.code
            or "stair" in issue.code
            or "support" in issue.code
        ],
    }

    # Deliberate one-run observation probe. The branch stays unmerged; CI's failure
    # exposes the exact deterministic LEGO result from the production Scene pipeline.
    raise AssertionError("BH233_OBSERVATION=" + json.dumps(summary, sort_keys=True))
