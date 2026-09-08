"""Architectural scene contracts and projection helpers."""
from .architectural_priors import (
    FR_OPENING_PRIOR_CATALOG_VERSION,
    OpeningPriorQuery,
    france_residential_opening_priors_v01,
)
from .modular_priors import (
    GLASS_BLOCK_PRIOR_CATALOG_VERSION,
    GlassBlockGridPriorQuery,
    glass_block_grid_prior_v01,
)
from .models import (
    Chimney, DeckBoardDirection, EdgeAccessSpan, EdgeTreatment, EquipmentType,
    Evidence, ExteriorMaterial, FacadeEquipment, FacadeVisibility, GradeProfile, Platform,
    PlatformEdge, PlatformEdges, PropertyValue, RoofPitchRange, SceneOpening, SceneRoof, SceneRoofType, SceneVolume, StairRun,
    SupportPost, Terrain, VisibilitySpan, VisibilityState,
)
from .photo_rectification import (
    NormalizedImagePoint,
    NormalizedImageQuadrilateral,
    PlanarPhotoRectification,
    rectified_plane_reference_annotation,
    rectify_photo_geometry_annotation,
    rectify_point,
)
from .photo_scale_cues import (
    PhotoGeometryAnnotation,
    PhotoScaleCueBinding,
    build_visual_scale_cues_from_photo_geometry,
    validate_photo_geometry_annotations,
)
from .platform_structure import PlatformStructureKind, PlatformStructureObservation
from .projection import ProjectionIssue, ProjectionResult, ProjectionSeverity
from .scale_estimation import (
    ArchitecturalDimensionPrior,
    ArchitecturalPriorProvenance,
    ArchitecturalScaleEstimate,
    ScaleCueVote,
    VisualScaleCue,
    estimate_architectural_scale,
)
from .survey_validation import SceneSurveyIssue, SceneSurveySeverity
from .topology import SceneRelation
from .wall_profile import WallProfileObservation
from .wall_profile_scene import ArchitecturalScene
from .multi_run_stair_fidelity import validate_scene_against_survey
from .multi_run_stair_geometry import (
    MultiRunStairGeometryFacts,
    MultiRunStairGeometryReport,
    StairRunJunction,
    analyze_multi_run_stair_geometry,
)
from .roof_geometry import (
    GableRoofGeometry,
    GableRoofPlane,
    RoofGeometryAssessment,
    RoofLine,
    derive_roof_geometry,
    derive_scene_roof_geometry,
)
from .spatial_analysis import (
    ChimneyBearingAssessment,
    SceneObjectEnvelope,
    SpatialPairFacts,
    SpatialRelationReport,
    analyze_scene_spatial_relations,
    scene_object_envelopes,
)
from .stair_spatial import (
    StairCorridor,
    StairEndpointContact,
    StairSpatialReport,
    analyze_stair_spatial,
)
from .topology_projection import project_scene_to_building
__all__=[
    "ArchitecturalDimensionPrior","ArchitecturalPriorProvenance","ArchitecturalScaleEstimate","ArchitecturalScene","Chimney","ChimneyBearingAssessment","DeckBoardDirection","EdgeAccessSpan","EdgeTreatment","EquipmentType","Evidence","ExteriorMaterial","FR_OPENING_PRIOR_CATALOG_VERSION","GLASS_BLOCK_PRIOR_CATALOG_VERSION",
    "FacadeEquipment","FacadeVisibility","GableRoofGeometry","GableRoofPlane","GlassBlockGridPriorQuery","GradeProfile","MultiRunStairGeometryFacts","MultiRunStairGeometryReport","NormalizedImagePoint","NormalizedImageQuadrilateral","OpeningPriorQuery","PhotoGeometryAnnotation","PhotoScaleCueBinding","PlanarPhotoRectification","Platform","PlatformEdge","PlatformEdges","PlatformStructureKind","PlatformStructureObservation","ProjectionIssue","ProjectionResult",
    "ProjectionSeverity","PropertyValue","RoofGeometryAssessment","RoofLine","RoofPitchRange","ScaleCueVote","SceneObjectEnvelope","SceneOpening","SceneRelation","SceneRoof","SceneRoofType","SceneSurveyIssue","SceneSurveySeverity","SceneVolume","SpatialPairFacts","SpatialRelationReport","StairCorridor","StairEndpointContact","StairRun","StairRunJunction","StairSpatialReport",
    "SupportPost","Terrain","VisibilitySpan","VisibilityState","VisualScaleCue","WallProfileObservation","analyze_multi_run_stair_geometry","analyze_scene_spatial_relations","analyze_stair_spatial","build_visual_scale_cues_from_photo_geometry","derive_roof_geometry","derive_scene_roof_geometry","estimate_architectural_scale","france_residential_opening_priors_v01","glass_block_grid_prior_v01","project_scene_to_building","rectified_plane_reference_annotation","rectify_photo_geometry_annotation","rectify_point","scene_object_envelopes","validate_photo_geometry_annotations","validate_scene_against_survey",
]
