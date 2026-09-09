"""Materialize a benchmark ArchitecturalScene recipe from a base Scene plus ordered overlays.

This is benchmark tooling, not production reconstruction logic. It only applies explicit
operations already serialized by benchmark evidence artifacts.
"""
from __future__ import annotations

import argparse
import json
from copy import deepcopy
from pathlib import Path

from brickhouse.scene import ArchitecturalScene


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def materialize_scene_recipe(recipe_path: Path, *, repository_root: Path) -> ArchitecturalScene:
    recipe_path = recipe_path.resolve()
    benchmark_dir = recipe_path.parent
    recipe = _load(recipe_path)
    base_scene_path = (benchmark_dir / recipe["base_scene"]).resolve()
    payload = _load(base_scene_path)

    for overlay_name in recipe.get("apply_overlays_in_order", []):
        overlay = _load(benchmark_dir / overlay_name)
        operation = overlay.get("operation")
        if operation == "replace_stair_system_geometry":
            replaced = set(overlay["replaces_scene_stair_ids"])
            payload["stairs"] = [item for item in payload.get("stairs", []) if item["id"] not in replaced]
            payload["stairs"].extend(deepcopy(overlay["stairs"]))
            payload["stair_system_links"] = deepcopy(overlay["stair_system_links"])
            updates = {item["relation_id"]: item for item in overlay["relation_updates"]}
            for relation in payload.get("relations", []):
                update = updates.get(relation["id"])
                if update:
                    relation.update({key: update[key] for key in ("subject_id", "object_id", "geometry_status", "statement")})
        elif operation == "update_platform_geometry":
            updates = {item["platform_id"]: item for item in overlay["platform_updates"]}
            for platform in payload.get("platforms", []):
                update = updates.get(platform["id"])
                if not update:
                    continue
                platform["position"]["z"] = update["position_z"]
                platform["source"] = deepcopy(update["source"])
                platform["evidence"] = deepcopy(update["evidence"])
                for support in platform.get("supports", []):
                    support["height"] = update["support_height"]
                    support["source"] = deepcopy(update["source"])
        else:
            raise ValueError(f"Unsupported benchmark Scene overlay operation: {operation!r}")

    payload["id"] = recipe["scene_id"]
    return ArchitecturalScene.model_validate(payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("recipe", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    scene = materialize_scene_recipe(args.recipe, repository_root=args.repository_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scene.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
