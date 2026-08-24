"""Architectural scene contracts and projection helpers."""
from .models import (
    ArchitecturalScene, Chimney, DeckBoardDirection, EdgeAccessSpan, EdgeTreatment, EquipmentType,
    Evidence, ExteriorMaterial, FacadeEquipment, FacadeVisibility, GradeProfile, Platform,
    PlatformEdge, PlatformEdges, PropertyValue, SceneOpening, SceneRoof, SceneRoofType, SceneVolume, StairRun,
    SupportPost, Terrain, VisibilitySpan, VisibilityState,
)
from .projection import ProjectionIssue, ProjectionResult, ProjectionSeverity, project_scene_to_building
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity
from .opening_visual_fidelity import validate_scene_against_survey
__all__=[
    "ArchitecturalScene","Chimney","DeckBoardDirection","EdgeAccessSpan","EdgeTreatment","EquipmentType","Evidence","ExteriorMaterial",
    "FacadeEquipment","FacadeVisibility","GradeProfile","Platform","PlatformEdge","PlatformEdges","ProjectionIssue","ProjectionResult",
    "ProjectionSeverity","PropertyValue","SceneOpening","SceneRoof","SceneRoofType","SceneSurveyIssue","SceneSurveySeverity","SceneVolume","StairRun",
    "SupportPost","Terrain","VisibilitySpan","VisibilityState","project_scene_to_building","validate_scene_against_survey",
]
