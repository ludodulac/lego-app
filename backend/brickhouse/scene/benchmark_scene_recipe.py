"""Deterministic materialization of serialized benchmark Scene recipes.

This module applies only explicit operations already recorded in benchmark artifacts. It does
not infer geometry and contains no benchmark-specific morphology or dimensions.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from pydantic import Field

from brickhouse.scene.models import ArchitecturalScene
from brickhouse.scene.stair_system_links import SceneStairSystemLink


class MaterializedBenchmarkScene(ArchitecturalScene):
    """ArchitecturalScene plus explicit benchmark-only provenance sidecars.

    ArchitecturalScene v0.2 predates the stair-system provenance sidecar added by
    BH-204. Materialization must not silently discard those links, because stair
    topology diagnostics consume them. This subtype preserves the sidecar without
    changing the accepted Survey or inventing any geometry.
    """

    stair_system_links: list[SceneStairSystemLink] = Field(default_factory=list)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def materialize_scene_recipe(recipe_path: Path) -> ArchitecturalScene:
    recipe_path = recipe_path.resolve()
    benchmark_dir = recipe_path.parent
    recipe = _load(recipe_path)
    payload = _load((benchmark_dir / recipe["base_scene"]).resolve())

    for overlay_name in recipe.get("apply_overlays_in_order", []):
        overlay = _load(benchmark_dir / overlay_name)
        operation = overlay.get("operation")

        if operation == "replace_stair_system_geometry":
            replaced = set(overlay["replaces_scene_stair_ids"])
            payload["stairs"] = [item for item in payload.get("stairs", []) if item["id"] not in replaced]
            payload["stairs"].extend(deepcopy(overlay["stairs"]))
            payload["stair_system_links"] = deepcopy(overlay["stair_system_links"])
            relation_updates = {item["relation_id"]: item for item in overlay["relation_updates"]}
            for relation in payload.get("relations", []):
                update = relation_updates.get(relation["id"])
                if update is not None:
                    relation.update(
                        {
                            key: update[key]
                            for key in ("subject_id", "object_id", "geometry_status", "statement")
                        }
                    )
            continue

        if operation == "update_platform_geometry":
            platform_updates = {item["platform_id"]: item for item in overlay["platform_updates"]}
            for platform in payload.get("platforms", []):
                update = platform_updates.get(platform["id"])
                if update is None:
                    continue
                platform["position"]["z"] = update["position_z"]
                platform["source"] = deepcopy(update["source"])
                platform["evidence"] = deepcopy(update["evidence"])
                for support in platform.get("supports", []):
                    support["height"] = update["support_height"]
                    support["source"] = deepcopy(update["source"])
            continue

        raise ValueError(f"Unsupported benchmark Scene overlay operation: {operation!r}")

    payload["id"] = recipe["scene_id"]
    return MaterializedBenchmarkScene.model_validate(payload)
