"""Architectural scene contracts and projection helpers."""
from .models import (
    Chimney, DeckBoardDirection, EdgeAccessSpan, EdgeTreatment, EquipmentType,
    Evidence, ExteriorMaterial, FacadeEquipment, FacadeVisibility, GradeProfile, Platform,
    PlatformEdge, PlatformEdges, PropertyValue, RoofPitchRange, SceneOpening, SceneRoof, SceneRoofType, SceneVolume, StairRun,
    SupportPost, Terrain, VisibilitySpan, VisibilityState,
)
from .platform_structure import PlatformStructureKind, PlatformStructureObservation
from .projection import ProjectionIssue, ProjectionResult, ProjectionSeverity
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity
from .topology import SceneRelation
from .wall_profile import WallProfileObservation
from .wall_profile_scene import ArchitecturalScene
from .platform_structure_fidelity import validate_scene_against_survey
from .topology_projection import project_scene_to_building
__all__=[
    "ArchitecturalScene","Chimney","DeckBoardDirection","EdgeAccessSpan","EdgeTreatment","EquipmentType","Evidence","ExteriorMaterial",
    "FacadeEquipment","FacadeVisibility","GradeProfile","Platform","PlatformEdge","PlatformEdges","PlatformStructureKind","PlatformStructureObservation","ProjectionIssue","ProjectionResult",
    "ProjectionSeverity","PropertyValue","RoofPitchRange","SceneOpening","SceneRelation","SceneRoof","SceneRoofType","SceneSurveyIssue","SceneSurveySeverity","SceneVolume","StairRun",
    "SupportPost","Terrain","VisibilitySpan","VisibilityState","WallProfileObservation","project_scene_to_building","validate_scene_against_survey",
]
