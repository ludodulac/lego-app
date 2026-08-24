"""Projection from ArchitecturalScene v0.2 to BuildingModel v0.1."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from brickhouse.building import BuildingModel, Metadata, Opening, Roof, RoofType, Volume, VolumeShape

from .models import ArchitecturalScene, SceneRoofType


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


def _roof_is_building_model_representable(roof) -> bool:
    if roof.type is SceneRoofType.FLAT:
        return True
    if roof.type is SceneRoofType.GABLE:
        return roof.ridge_direction is not None and roof.pitch_degrees is not None
    return False


def project_scene_to_building(scene: ArchitecturalScene) -> ProjectionResult:
    """Project every BuildingModel-representable scene object without silent simplification."""

    issues: list[ProjectionIssue] = []

    if scene.terrain and scene.terrain.profiles:
        issues.append(ProjectionIssue(code="terrain_not_supported", severity=ProjectionSeverity.WARNING, message="BuildingModel 0.1 uses a global flat ground plane; facade grade profiles are preserved only in scene data."))
        for profile in scene.terrain.profiles:
            if profile.start_elevation is None or profile.end_elevation is None:
                issues.append(
                    ProjectionIssue(
                        code="terrain_geometry_incomplete",
                        severity=ProjectionSeverity.WARNING,
                        object_id=f"terrain:{profile.facade.value}",
                        message=(
                            f"Terrain grade on facade {profile.facade.value!r} is architecturally observed, "
                            "but its metric endpoint elevations are incomplete. The rich Scene preserves the "
                            "unknown value and the LEGO pipeline must not invent a grade amplitude."
                        ),
                    )
                )

    if scene.visibility:
        issues.append(ProjectionIssue(code="visibility_not_supported", severity=ProjectionSeverity.WARNING, message="Facade visibility/occlusion spans constrain the ArchitecturalScene but are not represented in BuildingModel 0.1."))

    if scene.equipment:
        issues.append(ProjectionIssue(code="equipment_not_supported", severity=ProjectionSeverity.WARNING, message="Facade equipment such as gutters, downspouts, pipes, vents and antennas is preserved in scene data but omitted from M0 projection."))

    if any(opening.local_grade_clearance is not None for opening in scene.openings):
        issues.append(ProjectionIssue(code="local_grade_clearance_not_supported", severity=ProjectionSeverity.WARNING, message="Opening-to-local-ground clearances are preserved in ArchitecturalScene but BuildingModel 0.1 uses only global opening offsets."))

    for chimney in scene.chimneys:
        issues.append(ProjectionIssue(code="chimney_not_supported", severity=ProjectionSeverity.WARNING, object_id=chimney.id, message="Chimneys are not representable in BuildingModel 0.1 and will be omitted from M0 projection."))

    for platform in scene.platforms:
        issues.append(ProjectionIssue(code="platform_not_supported", severity=ProjectionSeverity.WARNING, object_id=platform.id, message="Exterior platforms/terraces are not representable in BuildingModel 0.1 and will be omitted."))

    for stair in scene.stairs:
        issues.append(ProjectionIssue(code="stair_not_supported", severity=ProjectionSeverity.WARNING, object_id=stair.id, message="Exterior stairs are not representable in BuildingModel 0.1 and will be omitted."))

    for roof in scene.roofs:
        if roof.type not in {SceneRoofType.FLAT, SceneRoofType.GABLE}:
            issues.append(
                ProjectionIssue(
                    code="roof_type_not_supported",
                    severity=ProjectionSeverity.WARNING,
                    object_id=roof.id,
                    message=f"ArchitecturalScene preserves roof type {roof.type.value!r}, but BuildingModel 0.1 can only project flat/gable roofs; this roof will remain Scene-only instead of being converted to a false gable/flat roof.",
                )
            )
        elif roof.type is SceneRoofType.GABLE and not _roof_is_building_model_representable(roof):
            missing = []
            if roof.ridge_direction is None:
                missing.append("ridge_direction")
            if roof.pitch_degrees is None:
                missing.append("pitch_degrees")
            issues.append(
                ProjectionIssue(
                    code="gable_geometry_incomplete",
                    severity=ProjectionSeverity.BLOCKER,
                    object_id=roof.id,
                    message=(
                        "ArchitecturalScene preserves a gable roof but does not know "
                        f"{', '.join(missing)}. BuildingModel 0.1 requires those fields, so LEGO projection "
                        "is blocked rather than inventing metric roof geometry or producing an open building."
                    ),
                )
            )

    # ArchitecturalScene may now preserve explicitly unknown envelope metrics.
    # BuildingModel/LEGO still need concrete dimensions, so block projection at
    # this boundary instead of forcing the Scene-producing model to invent them.
    for volume in scene.volumes:
        missing_metrics = [
            name
            for name in ("width", "depth", "height")
            if getattr(volume, name).value is None
        ]
        if missing_metrics:
            issues.append(
                ProjectionIssue(
                    code="volume_geometry_incomplete",
                    severity=ProjectionSeverity.BLOCKER,
                    object_id=volume.id,
                    message=(
                        f"ArchitecturalScene volume {volume.id!r} has unknown metric "
                        f"{', '.join(missing_metrics)}. Keep those values null rather than inventing them; "
                        "BuildingModel/LEGO projection requires a supported metric envelope."
                    ),
                )
            )
        if volume.floors > 3:
            issues.append(ProjectionIssue(code="building_model_floor_limit", severity=ProjectionSeverity.BLOCKER, object_id=volume.id, message="BuildingModel 0.1 supports at most three floors; projection will not silently clamp the scene value."))

    if any(issue.severity is ProjectionSeverity.BLOCKER for issue in issues):
        return ProjectionResult(building=None, issues=issues)

    volumes = [Volume(id=volume.id, shape=VolumeShape.RECTANGULAR_PRISM, position=volume.position, width=volume.width.value, depth=volume.depth.value, height=volume.height.value, floors=volume.floors, source=volume.source) for volume in scene.volumes]

    openings = [Opening(id=opening.id, type=opening.type, volume_id=opening.volume_id, facade=opening.facade, offset_horizontal=opening.offset_horizontal, offset_vertical=opening.offset_vertical, width=opening.width, height=opening.height, source=opening.source, window_style=opening.window_style, has_sill=opening.has_sill, has_decorative_surround=opening.has_decorative_surround) for opening in scene.openings]

    roofs = [
        Roof(
            id=roof.id,
            volume_id=roof.volume_id,
            type=RoofType(roof.type.value),
            overhang=roof.overhang,
            ridge_direction=roof.ridge_direction,
            pitch_degrees=roof.pitch_degrees,
            source=roof.source,
        )
        for roof in scene.roofs
        if _roof_is_building_model_representable(roof)
    ]

    notes = scene.notes
    if issues:
        loss = "; ".join(issue.code for issue in issues)
        notes = f"{notes + ' ' if notes else ''}Projection losses: {loss}."

    # ArchitecturalScene is intentionally generic. Do not inject a house-specific
    # classification merely because a visual regression fixture is a house.
    building = BuildingModel(schema_version="0.1", id=scene.id, name=scene.name, building_type="building", units="m", volumes=volumes, openings=openings, roofs=roofs, appearance=scene.appearance, metadata=Metadata(created_from="photo_analysis", notes=notes))
    return ProjectionResult(building=building, issues=issues)
