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
from .spatial_analysis import (
    SceneObjectEnvelope,
    SpatialPairFacts,
    SpatialRelationReport,
    analyze_scene_spatial_relations,
    scene_object_envelopes,
)
from .topology_projection import project_scene_to_building
__all__=[
    "ArchitecturalScene","Chimney","DeckBoardDirection","EdgeAccessSpan","EdgeTreatment","EquipmentType","Evidence","ExteriorMaterial",
    "FacadeEquipment","FacadeVisibility","GradeProfile","Platform","PlatformEdge","PlatformEdges","PlatformStructureKind","PlatformStructureObservation","ProjectionIssue","ProjectionResult",
    "ProjectionSeverity","PropertyValue","RoofPitchRange","SceneObjectEnvelope","SceneOpening","SceneRelation","SceneRoof","SceneRoofType","SceneSurveyIssue","SceneSurveySeverity","SceneVolume","SpatialPairFacts","SpatialRelationReport","StairRun",
    "SupportPost","Terrain","VisibilitySpan","VisibilityState","WallProfileObservation","analyze_scene_spatial_relations","project_scene_to_building","scene_object_envelopes","validate_scene_against_survey",
]
