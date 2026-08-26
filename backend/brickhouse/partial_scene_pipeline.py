"""Conservative LEGO preview for partially resolved ArchitecturalScene data.

This path exists so BrickHouse can show useful first bricks before every roof or
external junction is metrically resolved. It never chooses missing dimensions,
roof directions, roof pitches, or hidden connections, and it keeps approximate
photo-derived metrics visibly separate from measured fact.
"""
from __future__ import annotations

from brickhouse.building.models import BuildingModel, Metadata, Opening, Volume, VolumeShape
from brickhouse.bricks.discretization_report import build_discretization_quality
from brickhouse.bricks.export import BrickExportBundle, BrickExportFidelityIssue
from brickhouse.bricks.scale_optimizer import recommend_front_width_studs
from brickhouse.pipeline import DEFAULT_FRONT_WIDTH_STUDS, run_m0_pipeline_model
from brickhouse.scene.models import ArchitecturalScene
from brickhouse.scene.topology_projection import project_scene_to_building

SECONDARY_VOLUME_CONFIDENCE_MIN = 0.50
LOW_CONFIDENCE_WARNING = 0.65


def _is_resolved_volume(volume) -> bool:
    return (
        volume.width.value is not None
        and volume.depth.value is not None
        and volume.height.value is not None
        and volume.floors <= 3
    )


def _secondary_volume_confidence(volume) -> float:
    return min(
        volume.width.source.confidence,
        volume.depth.source.confidence,
        volume.height.source.confidence,
    )


def _selected_partial_volumes(scene: ArchitecturalScene):
    primary = scene.volumes[0]
    if not _is_resolved_volume(primary):
        raise ValueError(
            "Partial LEGO preview still needs the primary volume with resolved width, depth and height."
        )

    included = [primary]
    omitted = []
    for volume in scene.volumes[1:]:
        if not _is_resolved_volume(volume):
            omitted.append((volume, "unresolved metric envelope"))
            continue
        confidence = _secondary_volume_confidence(volume)
        if confidence < SECONDARY_VOLUME_CONFIDENCE_MIN:
            omitted.append((volume, f"metric confidence {confidence:.2f}"))
            continue
        included.append(volume)
    return included, omitted


def _resolved_core_building(scene: ArchitecturalScene) -> BuildingModel:
    """Project the primary envelope plus secondary volumes constrained well enough to preview."""
    resolved, _ = _selected_partial_volumes(scene)
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
                "Conservative partial LEGO preview: unresolved or weakly constrained secondary geometry, "
                "roof geometry and hidden exterior junctions are intentionally omitted rather than inferred."
            ),
        ),
    )


def _metric_uncertainty_issues(scene: ArchitecturalScene) -> list[BrickExportFidelityIssue]:
    included, omitted = _selected_partial_volumes(scene)
    included_ids = {volume.id for volume in included}
    issues: list[BrickExportFidelityIssue] = []

    for volume, reason in omitted:
        issues.append(
            BrickExportFidelityIssue(
                code="partial_preview_secondary_volume_omitted",
                severity="warning",
                object_id=volume.id,
                message=(
                    f"Secondary volume {volume.id!r} is visible in ArchitecturalScene but is omitted from the "
                    f"first-bricks preview because its envelope is still weakly constrained ({reason})."
                ),
            )
        )

    for volume in included:
        for name in ("width", "depth", "height"):
            value = getattr(volume, name)
            if value.source.kind == "user_provided" or value.source.confidence >= LOW_CONFIDENCE_WARNING:
                continue
            issues.append(
                BrickExportFidelityIssue(
                    code="low_confidence_partial_dimension",
                    severity="warning" if value.source.confidence < 0.5 else "info",
                    object_id=volume.id,
                    message=(
                        f"{volume.id}.{name}={value.value:g} m is used provisionally in the first-bricks preview "
                        f"from photo inference confidence {value.source.confidence:.2f}; it is not a measured dimension."
                    ),
                )
            )

    for opening in scene.openings:
        if opening.volume_id not in included_ids:
            continue
        if opening.source.kind == "user_provided" or opening.source.confidence >= LOW_CONFIDENCE_WARNING:
            continue
        issues.append(
            BrickExportFidelityIssue(
                code="low_confidence_partial_opening_geometry",
                severity="warning" if opening.source.confidence < 0.4 else "info",
                object_id=opening.id,
                message=(
                    f"Opening {opening.id!r} is kept as a real wall cut, but its current rectangle is photo-derived "
                    f"at confidence {opening.source.confidence:.2f}; later cross-view constraints may move or resize it."
                ),
            )
        )
    return issues


def _partial_fidelity_issues(scene: ArchitecturalScene) -> list[BrickExportFidelityIssue]:
    projection = project_scene_to_building(scene)
    issues = [*_metric_uncertainty_issues(scene)]
    issues.extend(
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
    )
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
    """Build the useful known subset while exposing every provisional metric as such."""
    if front_width_studs <= 0:
        raise ValueError("front_width_studs must be positive")
    building = _resolved_core_building(scene)
    bundle = run_m0_pipeline_model(building, front_width_studs=front_width_studs)
    quality = build_discretization_quality(building, front_width_studs=front_width_studs)
    recommendation = recommend_front_width_studs(
        building,
        preferred_front_width_studs=front_width_studs,
        search_radius_studs=6,
    )
    metadata = bundle.metadata.model_copy(update={
        "discretization_quality": quality,
        "scale_recommendation": recommendation,
    })
    return bundle.model_copy(update={
        "metadata": metadata,
        "fidelity_issues": _partial_fidelity_issues(scene),
    })