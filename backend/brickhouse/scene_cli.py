"""CLI entry point for building a validated ArchitecturalScene directly into LEGO output."""
from __future__ import annotations

import argparse
from pathlib import Path

from brickhouse.bricks.export import BrickExportBundle, export_bundle_json
from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.pipeline import DEFAULT_FRONT_WIDTH_STUDS, run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


def load_architectural_scene(path: str | Path) -> ArchitecturalScene:
    source = Path(path)
    return ArchitecturalScene.model_validate_json(source.read_text(encoding="utf-8"))


def write_scene_export(
    input_path: str | Path,
    output_path: str | Path,
    *,
    front_width_studs: int = DEFAULT_FRONT_WIDTH_STUDS,
    allow_partial: bool = False,
) -> BrickExportBundle:
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")
    scene = load_architectural_scene(input_path)
    builder = run_partial_scene_pipeline if allow_partial else run_m0_pipeline_scene
    bundle = builder(scene, front_width_studs=front_width_studs)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(export_bundle_json(bundle) + "\n", encoding="utf-8")
    return bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="brickhouse-scene-build",
        description=(
            "Generate BrickModel/BOM/AssemblyPlan JSON directly from an ArchitecturalScene v0.2. "
            "Strict mode is the default; --allow-partial emits only trustworthy resolved geometry."
        ),
    )
    parser.add_argument("input", type=Path, help="ArchitecturalScene v0.2 JSON input")
    parser.add_argument("output", type=Path, help="Output LEGO export JSON path")
    parser.add_argument(
        "--front-width-studs",
        type=int,
        default=DEFAULT_FRONT_WIDTH_STUDS,
        help=f"target front facade width in studs (default: {DEFAULT_FRONT_WIDTH_STUDS})",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help=(
            "build only resolved envelope/opening geometry when roof or exterior junctions remain unknown; "
            "unknown geometry is omitted and reported instead of guessed"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bundle = write_scene_export(
        args.input,
        args.output,
        front_width_studs=args.front_width_studs,
        allow_partial=args.allow_partial,
    )
    print(
        f"Generated {args.output}: {bundle.bom.total_parts} parts, "
        f"{bundle.bom.unique_part_types} canonical types, "
        f"{bundle.assembly_plan.total_steps if bundle.assembly_plan else 0} assembly steps"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
