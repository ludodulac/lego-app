"""CLI entry point for building a validated ArchitecturalScene directly into LEGO output."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from brickhouse.bricks.export import BrickExportBundle, export_bundle_json
from brickhouse.building.models import OpeningVisualDescription
from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.pipeline import DEFAULT_FRONT_WIDTH_STUDS, run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


def load_architectural_scene(path: str | Path) -> ArchitecturalScene:
    source = Path(path)
    return ArchitecturalScene.model_validate_json(source.read_text(encoding="utf-8"))


def apply_opening_visual_evidence(
    scene: ArchitecturalScene,
    evidence_path: str | Path,
) -> ArchitecturalScene:
    """Overlay explicitly supplied opening_visual fields onto matching Scene openings.

    The evidence file may carry provenance fields beside the visual payload. Only
    fields defined by OpeningVisualDescription are applied; existing visual fields
    not mentioned by an observation are preserved. Unknown opening ids fail loudly.
    """
    source = Path(evidence_path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    observations = payload.get("observations")
    if not isinstance(observations, list):
        raise ValueError("opening visual evidence must contain an observations list")

    visual_fields = set(OpeningVisualDescription.model_fields)
    openings_by_id = {opening.id: opening for opening in scene.openings}
    updated_openings = list(scene.openings)
    index_by_id = {opening.id: index for index, opening in enumerate(scene.openings)}

    for observation in observations:
        if not isinstance(observation, dict):
            raise ValueError("opening visual evidence observations must be objects")
        opening_id = observation.get("opening_id")
        if not isinstance(opening_id, str) or not opening_id:
            raise ValueError("opening visual evidence observation requires opening_id")
        opening = openings_by_id.get(opening_id)
        if opening is None:
            raise ValueError(f"opening visual evidence references unknown opening id {opening_id!r}")

        explicit_visual = {key: value for key, value in observation.items() if key in visual_fields}
        if not explicit_visual:
            continue
        previous = opening.opening_visual.model_dump(exclude_none=True) if opening.opening_visual is not None else {}
        merged = OpeningVisualDescription.model_validate({**previous, **explicit_visual})
        updated_openings[index_by_id[opening_id]] = opening.model_copy(update={"opening_visual": merged})

    return scene.model_copy(update={"openings": updated_openings})


def write_scene_export(
    input_path: str | Path,
    output_path: str | Path,
    *,
    front_width_studs: int = DEFAULT_FRONT_WIDTH_STUDS,
    allow_partial: bool = False,
    optimize_scale: bool = False,
    opening_visual_evidence: str | Path | None = None,
) -> BrickExportBundle:
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")
    if optimize_scale and not allow_partial:
        raise ValueError("optimize_scale currently requires allow_partial")
    scene = load_architectural_scene(input_path)
    if opening_visual_evidence is not None:
        scene = apply_opening_visual_evidence(scene, opening_visual_evidence)
    if allow_partial:
        bundle = run_partial_scene_pipeline(
            scene,
            front_width_studs=front_width_studs,
            optimize_scale=optimize_scale,
        )
    else:
        bundle = run_m0_pipeline_scene(scene, front_width_studs=front_width_studs)
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
        help=f"preferred front facade width in studs (default: {DEFAULT_FRONT_WIDTH_STUDS})",
    )
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help=(
            "build only resolved envelope/opening geometry when roof or exterior junctions remain unknown; "
            "unknown geometry is omitted and reported instead of guessed"
        ),
    )
    parser.add_argument(
        "--optimize-scale",
        action="store_true",
        help=(
            "with --allow-partial, test nearby LEGO scales and apply the recommendation only when "
            "the measured grid-error score improves by at least 10 percent"
        ),
    )
    parser.add_argument(
        "--opening-visual-evidence",
        type=Path,
        help=(
            "optional JSON overlay whose observations target Scene opening ids and update only "
            "explicit opening_visual fields"
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
        optimize_scale=args.optimize_scale,
        opening_visual_evidence=args.opening_visual_evidence,
    )
    print(
        f"Generated {args.output}: {bundle.bom.total_parts} parts, "
        f"{bundle.bom.unique_part_types} canonical types, "
        f"{bundle.assembly_plan.total_steps if bundle.assembly_plan else 0} assembly steps"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
