"""End-to-end M0 pipeline from BuildingModel or ArchitecturalScene to viewer export JSON."""
from __future__ import annotations

import argparse
from pathlib import Path

from brickhouse.building.models import BuildingModel, RoofType
from brickhouse.building.validation import load_building_model
from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel, generate_brick_model
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.export import (
    BrickExportBundle,
    BrickExportFidelityIssue,
    create_export_bundle,
    export_bundle_json,
)
from brickhouse.bricks.facade_details import generate_window_surrounds
from brickhouse.bricks.piece_capabilities import (
    create_current_engine_capability_registry,
    validate_model_part_capabilities,
)
from brickhouse.bricks.roof import generate_spatial_gable_roof, select_roof_slope_family
from brickhouse.bricks.scaling import COURSES_PER_STUD_RATIO
from brickhouse.bricks.scene_architecture import augment_brick_model_with_scene_architecture
from brickhouse.bricks.scene_glazing import augment_brick_model_with_scene_glazing
from brickhouse.bricks.scene_materials import apply_scene_part_categories
from brickhouse.bricks.spatial import generate_spatial_brick_shell
from brickhouse.bricks.windows import generate_window_assemblies
from brickhouse.geometry import generate_building_geometry
from brickhouse.scene.models import ArchitecturalScene, SceneRoofType
from brickhouse.scene.topology_projection import project_scene_to_building
from brickhouse.vision.compatibility import assess_m0_compatibility

DEFAULT_FRONT_WIDTH_STUDS = 48

# These Scene properties temporarily disappear in BuildingModel 0.1 but are added
# back by Scene-aware LEGO augmentation later in the same pipeline. They must not
# be reported as final export losses.
_SCENE_LOSSES_RECOVERED_AFTER_PROJECTION = {
    "terrain_not_supported",
    "local_grade_clearance_not_supported",
    "platform_not_supported",
    "stair_not_supported",
    "chimney_not_supported",
}


def _validate_generated_model(model: BrickModel) -> None:
    """Final safety gate: catalogue presence alone never authorizes a LEGO part."""
    validate_model_part_capabilities(
        model,
        create_current_engine_capability_registry(),
    )


def _volume_geometry(geometry, volume_id: str):
    return geometry.model_copy(
        update={
            "walls": [wall for wall in geometry.walls if wall.volume_id == volume_id],
            "roof_planes": [
                plane for plane in geometry.roof_planes if plane.volume_id == volume_id
            ],
        }
    )


def _translate_model(
    model: BrickModel,
    *,
    prefix: str,
    x: int,
    y: int,
    z: int,
):
    return [
        part.model_copy(
            update={
                "placement_id": f"{prefix}:{part.placement_id}",
                "x_studs": part.x_studs + x,
                "y_studs": part.y_studs + y,
                "z_plates": part.z_plates + z,
            }
        )
        for part in model.parts
    ]


def _single_volume_bundle(
    building: BuildingModel,
    geometry,
    front_width_studs: int,
) -> BrickExportBundle:
    shell = generate_building_brick_shell(geometry, front_width_studs)
    spatial_shell = generate_spatial_brick_shell(shell)
    window_parts, fitted_window_ids = generate_window_assemblies(building, shell)
    facade_details = generate_window_surrounds(
        building,
        shell,
        skip_opening_ids=fitted_window_ids,
    )
    roof = building.roofs[0] if building.roofs else None
    spatial_roof = (
        generate_spatial_gable_roof(geometry, shell)
        if roof is not None and roof.type is RoofType.GABLE
        else None
    )
    brick_model = generate_brick_model(
        spatial_shell,
        spatial_roof,
        facade_details,
        window_parts,
    )
    _validate_generated_model(brick_model)
    bom = generate_bom(brick_model)
    assembly_plan = generate_assembly_plan(brick_model)
    return create_export_bundle(
        brick_model,
        bom,
        assembly_plan,
        appearance=building.appearance,
    )


def run_m0_pipeline_model(
    building: BuildingModel,
    *,
    front_width_studs: int = DEFAULT_FRONT_WIDTH_STUDS,
) -> BrickExportBundle:
    """Run M0 on one or more rectangular volumes using one shared global scale."""
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")

    geometry = generate_building_geometry(building)
    if len(building.volumes) == 1:
        return _single_volume_bundle(building, geometry, front_width_studs)

    primary = building.volumes[0]
    studs_per_meter = front_width_studs / primary.width
    plates_per_meter = studs_per_meter * COURSES_PER_STUD_RATIO * 3
    min_x = min(volume.position.x for volume in building.volumes)
    min_y = min(volume.position.y for volume in building.volumes)
    min_z = min(volume.position.z for volume in building.volumes)
    roofs_by_volume = {roof.volume_id: roof for roof in building.roofs}
    all_parts = []
    max_x = max_y = max_z = 1

    for volume in building.volumes:
        subgeometry = _volume_geometry(geometry, volume.id)
        shell = generate_building_brick_shell(
            subgeometry,
            studs_per_meter=studs_per_meter,
        )
        spatial_shell = generate_spatial_brick_shell(shell)
        window_parts, fitted_window_ids = generate_window_assemblies(building, shell)
        facade_details = generate_window_surrounds(
            building,
            shell,
            skip_opening_ids=fitted_window_ids,
        )
        roof = roofs_by_volume.get(volume.id)
        spatial_roof = (
            generate_spatial_gable_roof(subgeometry, shell)
            if roof is not None and roof.type is RoofType.GABLE
            else None
        )
        local_model = generate_brick_model(
            spatial_shell,
            spatial_roof,
            facade_details,
            window_parts,
        )
        x = round((volume.position.x - min_x) * studs_per_meter)
        y = round((volume.position.y - min_y) * studs_per_meter)
        z = round((volume.position.z - min_z) * plates_per_meter)
        all_parts.extend(
            _translate_model(local_model, prefix=volume.id, x=x, y=y, z=z)
        )
        max_x = max(max_x, x + local_model.width_studs)
        max_y = max(max_y, y + local_model.depth_studs)
        max_z = max(max_z, z + local_model.height_plates)

    brick_model = BrickModel(
        building_id=building.id,
        volume_id="composite",
        width_studs=max_x,
        depth_studs=max_y,
        height_plates=max_z,
        parts=all_parts,
    )
    _validate_generated_model(brick_model)
    bom = generate_bom(brick_model)
    assembly_plan = generate_assembly_plan(brick_model)
    return create_export_bundle(
        brick_model,
        bom,
        assembly_plan,
        appearance=building.appearance,
    )


def _source_confidence_issue(kind: str, obj) -> BrickExportFidelityIssue | None:
    """Surface architectural uncertainty instead of presenting inferred geometry as measured fact."""
    source = getattr(obj, "source", None)
    if source is None or source.kind == "user_provided" or source.confidence >= 0.65:
        return None
    severity = "warning" if source.confidence < 0.5 else "info"
    return BrickExportFidelityIssue(
        code="low_confidence_exterior_geometry",
        severity=severity,
        object_id=obj.id,
        message=(
            f"{kind} {obj.id!r} is rendered from inferred architectural geometry "
            f"with confidence {source.confidence:.2f}. Additional overlapping views may refine "
            "its position or connectivity; the current LEGO geometry must not be treated as measured fact."
        ),
    )


def _scene_export_fidelity_issues(
    scene: ArchitecturalScene,
    projection,
) -> list[BrickExportFidelityIssue]:
    """Describe losses that remain in the FINAL LEGO result, not temporary projection gaps."""
    issues: list[BrickExportFidelityIssue] = []

    for issue in projection.issues:
        if issue.code in _SCENE_LOSSES_RECOVERED_AFTER_PROJECTION:
            continue
        severity = "blocker" if issue.severity.value == "blocker" else "warning"
        if issue.code == "visibility_not_supported":
            severity = "info"
        issues.append(
            BrickExportFidelityIssue(
                code=issue.code,
                severity=severity,
                message=issue.message,
                object_id=issue.object_id,
            )
        )

    # Scene-aware structures survive projection, but their metric topology may
    # still be an inference. Keep that uncertainty visible in the final result.
    for platform in scene.platforms:
        issue = _source_confidence_issue("Platform", platform)
        if issue is not None:
            issues.append(issue)
    for stair in scene.stairs:
        issue = _source_confidence_issue("StairRun", stair)
        if issue is not None:
            issues.append(issue)
    for chimney in scene.chimneys:
        issue = _source_confidence_issue("Chimney", chimney)
        if issue is not None:
            issues.append(issue)

    # A gable can be constructed while still using the closest validated LEGO
    # slope family. Report that approximation rather than pretending its pitch
    # is architecturally exact.
    for roof in scene.roofs:
        if roof.type is not SceneRoofType.GABLE or roof.pitch_degrees is None:
            continue
        family = select_roof_slope_family(roof.pitch_degrees)
        delta = abs(family.pitch_degrees - roof.pitch_degrees)
        if delta > 0.25:
            issues.append(
                BrickExportFidelityIssue(
                    code="roof_pitch_quantized",
                    severity="info" if delta <= 5 else "warning",
                    object_id=roof.id,
                    message=(
                        f"Roof pitch {roof.pitch_degrees:g}° is preserved in ArchitecturalScene; "
                        f"the current LEGO build uses the validated {family.pitch_degrees:g}° "
                        f"slope family (difference {delta:g}°)."
                    ),
                )
            )

    compatibility = assess_m0_compatibility(projection.building)
    for warning in compatibility.warnings:
        issues.append(
            BrickExportFidelityIssue(
                code="m0_model_warning",
                severity="warning",
                message=warning,
            )
        )
    for blocker in compatibility.blockers:
        issues.append(
            BrickExportFidelityIssue(
                code="m0_model_blocker",
                severity="blocker",
                message=blocker,
            )
        )

    unique = []
    seen = set()
    for issue in issues:
        key = (issue.code, issue.object_id, issue.message)
        if key not in seen:
            seen.add(key)
            unique.append(issue)
    return unique


def run_m0_pipeline_scene(
    scene: ArchitecturalScene,
    *,
    front_width_studs: int = DEFAULT_FRONT_WIDTH_STUDS,
) -> BrickExportBundle:
    """Build the rich Scene and report anything the final LEGO model still loses."""
    projection = project_scene_to_building(scene)
    if projection.building is None or projection.blocked:
        blockers = " ".join(
            issue.message
            for issue in projection.issues
            if issue.severity.value == "blocker"
        )
        raise ValueError(blockers or "ArchitecturalScene cannot be projected to BuildingModel")

    fidelity_issues = _scene_export_fidelity_issues(scene, projection)
    base = run_m0_pipeline_model(
        projection.building,
        front_width_studs=front_width_studs,
    )
    enriched = augment_brick_model_with_scene_architecture(
        base.brick_model,
        scene,
        front_width_studs=front_width_studs,
    )
    enriched = apply_scene_part_categories(enriched, scene)
    enriched = augment_brick_model_with_scene_glazing(
        enriched,
        scene,
        front_width_studs=front_width_studs,
    )
    _validate_generated_model(enriched)

    if enriched is base.brick_model:
        return base.model_copy(update={"fidelity_issues": fidelity_issues})

    bom = generate_bom(enriched)
    assembly_plan = generate_assembly_plan(enriched)
    return create_export_bundle(
        enriched,
        bom,
        assembly_plan,
        appearance=projection.building.appearance,
        fidelity_issues=fidelity_issues,
    )


def run_m0_pipeline(
    input_path: str | Path,
    *,
    front_width_studs: int = DEFAULT_FRONT_WIDTH_STUDS,
) -> BrickExportBundle:
    building = load_building_model(input_path)
    return run_m0_pipeline_model(building, front_width_studs=front_width_studs)


def write_m0_export(
    input_path: str | Path,
    output_path: str | Path,
    *,
    front_width_studs: int = DEFAULT_FRONT_WIDTH_STUDS,
) -> BrickExportBundle:
    bundle = run_m0_pipeline(input_path, front_width_studs=front_width_studs)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(export_bundle_json(bundle) + "\n", encoding="utf-8")
    return bundle


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="brickhouse-m0",
        description=(
            "Generate a BrickHouse M0 BrickModel/BOM/AssemblyPlan JSON export "
            "from a BuildingModel JSON file."
        ),
    )
    parser.add_argument("input", type=Path, help="BuildingModel JSON input")
    parser.add_argument("output", type=Path, help="Output export JSON path")
    parser.add_argument(
        "--front-width-studs",
        type=int,
        default=DEFAULT_FRONT_WIDTH_STUDS,
        help=f"target front facade width in studs (default: {DEFAULT_FRONT_WIDTH_STUDS})",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bundle = write_m0_export(
        args.input,
        args.output,
        front_width_studs=args.front_width_studs,
    )
    print(
        f"Generated {args.output}: {bundle.bom.total_parts} parts, "
        f"{bundle.bom.unique_part_types} canonical types, "
        f"{bundle.assembly_plan.total_steps if bundle.assembly_plan else 0} assembly steps"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
