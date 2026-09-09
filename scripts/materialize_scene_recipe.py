"""Materialize a benchmark ArchitecturalScene recipe and optionally write it as JSON."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("recipe", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    scene = materialize_scene_recipe(args.recipe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(scene.model_dump(mode="json"), indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
