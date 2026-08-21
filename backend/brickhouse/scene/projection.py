"""Projection from ArchitecturalScene v0.2 to BuildingModel v0.1."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from brickhouse.building import BuildingModel, Metadata, Opening, Roof, Volume, VolumeShape

from .models import ArchitecturalScene


class ProjectionSeverity(str, Enum):
    WARNING = "warning"
    BLOCKER = "blocker"


class ProjectionIssue(BaseModel):
    code: str
    severity: ProjectionSeverity
    message: str
    object_id: str | None = None


class ProjectionResult(BaseModel):
    building: BuildingModel | None
    issues: list[ProjectionIssue] = Field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return any(issue.severity is ProjectionSeverity.BLOCKER for issue in self.issues)


def project_scene_to_building(scene: ArchitecturalScene) -> ProjectionResult:
    """Project representable scene data into BuildingModel 0.1 with explicit information loss."""

    issues: list[ProjectionIssue] = []

    if scene.terrain and scene.terrain.profiles:
        issues.append(
            ProjectionIssue(
                code="terrain_not_supported",
                severity=ProjectionSeverity.WARNING,
                message="BuildingModel 0.1 uses a global flat ground plane; facade grade profiles are preserved only in scene data.",
            )
        )

    for chimney in scene.chimneys:
        issues.append(
            ProjectionIssue(
                code="chimney_not_supported",
                severity=ProjectionSeverity.WARNING,
                object_id=chimney.id,
                message="Chimneys are not representable in BuildingModel 0.1 and will be omitted from M0 projection.",
            )
        )

    for platform in scene.platforms:
        issues.append(
            ProjectionIssue(
                code="platform_not_supported",
                severity=ProjectionSeverity.WARNING,
                object_id=platform.id,
                message="Exterior platforms/terraces are not representable in BuildingModel 0.1 and will be omitted.",
            )
        )

    for stair in scene.stairs:
        issues.append(
            ProjectionIssue(
                code="stair_not_supported",
                severity=ProjectionSeverity.WARNING,
                object_id=stair.id,
                message="Exterior stairs are not representable in BuildingModel 0.1 and will be omitted.",
            )
        )

    if len(scene.volumes) != 1:
        issues.append(
            ProjectionIssue(
                code="m0_single_volume_only",
                severity=ProjectionSeverity.BLOCKER,
                message="Current M0 projection requires exactly one principal building volume.",
            )
        )

    if len(scene.roofs) > 1:
        issues.append(
            ProjectionIssue(
                code="m0_single_roof_only",
                severity=ProjectionSeverity.BLOCKER,
                message="Current M0 projection supports at most one roof.",
            )
        )

    for volume in scene.volumes:
        if volume.floors > 3:
            issues.append(
                ProjectionIssue(
                    code="building_model_floor_limit",
                    severity=ProjectionSeverity.BLOCKER,
                    object_id=volume.id,
                    message="BuildingModel 0.1 supports at most three floors; projection will not silently clamp the scene value.",
                )
            )

    if any(issue.severity is ProjectionSeverity.BLOCKER for issue in issues):
        return ProjectionResult(building=None, issues=issues)

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
        for volume in scene.volumes
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
    ]

    roofs = [
        Roof(
            id=roof.id,
            volume_id=roof.volume_id,
            type=roof.type,
            overhang=roof.overhang,
            ridge_direction=roof.ridge_direction,
            pitch_degrees=roof.pitch_degrees,
            source=roof.source,
        )
        for roof in scene.roofs
    ]

    notes = scene.notes
    if issues:
        loss = "; ".join(issue.code for issue in issues)
        notes = f"{notes + ' ' if notes else ''}Projection losses: {loss}."

    building = BuildingModel(
        schema_version="0.1",
        id=scene.id,
        name=scene.name,
        building_type="house",
        units="m",
        volumes=volumes,
        openings=openings,
        roofs=roofs,
        appearance=scene.appearance,
        metadata=Metadata(created_from="photo_analysis", notes=notes),
    )
    return ProjectionResult(building=building, issues=issues)
