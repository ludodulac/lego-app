"""Conservative LEGO preview for partially resolved ArchitecturalScene data.

This path exists so BrickHouse can show trustworthy bricks before every roof or
external junction is metrically resolved.  It never chooses missing dimensions,
roof directions, roof pitches, or hidden connections.
"""
from __future__ import annotations

from brickhouse.building.models import BuildingModel, Metadata, Opening, Volume, VolumeShape
from brickhouse.bricks.export import BrickExportBundle, BrickExportFidelityIssue
from brickhouse.pipeline import DEFAULT_FRONT_WIDTH_STUDS, run_m0_pipeline_model
from brickhouse.scene.models import ArchitecturalScene
from brickhouse.scene.topology_projection import project_scene_to_building


def _resolved_core_building(scene: ArchitecturalScene) -> BuildingModel:
    """Project only metric envelope/opening facts that are already resolved."""
    resolved = [
        volume
        for volume in scene.volumes
        if volume.width.value is not None
        and volume.depth.value is not None
        and volume.height.value is not None
        and volume.floors <= 3
    ]
    if not resolved:
        raise ValueError(
            "Partial LEGO preview still needs at least one volume with resolved width, depth and height."
        )

    resolved_ids = {volume.id for volume in resolved}
    volumes = [
        Volume(
            id=volume.id,
            shape=VolumeShape.RECTANGULAR_PRISM,
            position=volume.position,
            width=volume.width.value,
            depth=volume.depth.value,
            height=volume.height.value,
            floors=volume.floors,
            source=volume.source,
        )
        for volume in resolved
    ]
    openings = [
        Opening(
            id=opening.id,
            type=opening.type,
            volume_id=opening.volume_id,
            facade=opening.facade,
            offset_horizontal=opening.offset_horizontal,
            offset_vertical=opening.offset_vertical,
            width=opening.width,
            height=opening.height,
            source=opening.source,
            window_style=opening.window_style,
            has_sill=opening.has_sill,
            has_decorative_surround=opening.has_decorative_surround,
        )
        for opening in scene.openings
        if opening.volume_id in resolved_ids
    ]
    return BuildingModel(
        schema_version="0.1",
        id=scene.id,
        name=scene.name,
        building_type="building",
        units="m",
        volumes=volumes,
        openings=openings,
        roofs=[],
        appearance=scene.appearance,
        metadata=Metadata(
            created_from="photo_analysis",
            notes=(
                "Conservative partial LEGO preview: unresolved roof and exterior junction geometry "
                "is intentionally omitted rather than inferred."
            ),
        ),
    )


def _partial_fidelity_issues(scene: ArchitecturalScene) -> list[BrickExportFidelityIssue]:
    projection = project_scene_to_building(scene)
    issues = [
        BrickExportFidelityIssue(
            code=issue.code,
            severity="warning" if issue.severity.value == "blocker" else "info",
            object_id=issue.object_id,
            message=(
                f"Partial preview omission: {issue.message}"
                if issue.severity.value == "blocker"
                else issue.message
            ),
        )
        for issue in projection.issues
    ]
    if scene.roofs:
        issues.append(
            BrickExportFidelityIssue(
                code="partial_preview_roof_omitted",
                severity="warning",
                message=(
                    "The partial LEGO preview intentionally leaves the roof open until its construction "
                    "geometry is resolved strongly enough to choose real LEGO slope parts."
                ),
            )
        )
    if scene.platforms or scene.stairs or scene.chimneys:
        issues.append(
            BrickExportFidelityIssue(
                code="partial_preview_exterior_details_omitted",
                severity="info",
                message=(
                    "Terraces, stairs and chimneys are kept in ArchitecturalScene but omitted from this first "
                    "core-shell preview so unresolved exterior connections cannot be fabricated."
                ),
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


def run_partial_scene_pipeline(
    scene: ArchitecturalScene,
    *,
    front_width_studs: int = DEFAULT_FRONT_WIDTH_STUDS,
) -> BrickExportBundle:
    """Build the trustworthy envelope/opening subset and its ordered assembly plan."""
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")
    building = _resolved_core_building(scene)
    bundle = run_m0_pipeline_model(building, front_width_studs=front_width_studs)
    return bundle.model_copy(update={"fidelity_issues": _partial_fidelity_issues(scene)})
