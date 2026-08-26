"""Evidence-first contract for independent multi-view architectural analysis.

This layer deliberately sits before ArchitecturalSurvey/ArchitecturalScene. It records
what each photo visibly supports, what is inferred, and what remains unknown without
requiring metric geometry or silently resolving contradictions.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class VisualStatus(str, Enum):
    OBSERVED = "observed"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class VisualCategory(str, Enum):
    OPENING = "opening"
    ROOF = "roof"
    WALL = "wall"
    TERRAIN = "terrain"
    PLATFORM = "platform"
    STAIR = "stair"
    SUPPORT = "support"
    RAILING = "railing"
    CHIMNEY = "chimney"
    EQUIPMENT = "equipment"
    NEIGHBOR = "neighbor"
    OTHER = "other"


class VisualEvidence(BaseModel):
    photo_index: int = Field(ge=1)
    observation: str = Field(min_length=1)


class VisualObservation(BaseModel):
    id: str = Field(min_length=1)
    category: VisualCategory
    status: VisualStatus
    statement: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[VisualEvidence] = Field(default_factory=list)


class PhotoAnalysis(BaseModel):
    photo_index: int = Field(ge=1)
    observations: list[VisualObservation] = Field(default_factory=list)

    @model_validator(mode="after")
    def evidence_stays_on_photo(self) -> "PhotoAnalysis":
        for observation in self.observations:
            if any(item.photo_index != self.photo_index for item in observation.evidence):
                raise ValueError("cold per-photo observations may cite only their own photo")
        return self


class ConsolidatedObject(BaseModel):
    id: str = Field(min_length=1)
    category: VisualCategory
    status: VisualStatus
    statement: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    photo_indices: list[int] = Field(default_factory=list)
    bounded_properties: dict[str, Any] = Field(default_factory=dict)
    components: dict[str, Any] = Field(default_factory=dict)


class SpatialRelation(BaseModel):
    id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    subject_id: str = Field(min_length=1)
    object_id: str = Field(min_length=1)
    status: VisualStatus
    confidence: float = Field(ge=0.0, le=1.0)
    statement: str | None = None
    evidence: list[VisualEvidence] = Field(default_factory=list)


class Contradiction(BaseModel):
    id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    photo_indices: list[int] = Field(default_factory=list)
    severity: str | None = None


class UnresolvedQuestion(BaseModel):
    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    photo_indices: list[int] = Field(default_factory=list)


class CurrentComparison(BaseModel):
    confirmed_current_claims: list[dict[str, Any]] = Field(default_factory=list)
    missing_from_current: list[dict[str, Any]] = Field(default_factory=list)
    possibly_wrong_current: list[dict[str, Any]] = Field(default_factory=list)
    current_claims_not_verifiable_from_photos: list[dict[str, Any]] = Field(default_factory=list)
    recommended_scene_changes: list[dict[str, Any]] = Field(default_factory=list)


class IndependentVisualAnalysis(BaseModel):
    schema_version: Literal["independent-visual-analysis-0.1"]
    photo_analyses: list[PhotoAnalysis] = Field(min_length=1)
    consolidated_objects: list[ConsolidatedObject] = Field(default_factory=list)
    spatial_relations: list[SpatialRelation] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    unresolved_questions: list[UnresolvedQuestion] = Field(default_factory=list)
    comparison_to_current: CurrentComparison = Field(default_factory=CurrentComparison)

    @model_validator(mode="after")
    def validate_photo_identity(self) -> "IndependentVisualAnalysis":
        photo_indices = [item.photo_index for item in self.photo_analyses]
        if len(photo_indices) != len(set(photo_indices)):
            raise ValueError("each source photo may have only one cold-analysis section")
        known = set(photo_indices)
        for item in self.consolidated_objects:
            if any(index not in known for index in item.photo_indices):
                raise ValueError("consolidated object references an unknown photo")
        for relation in self.spatial_relations:
            if any(item.photo_index not in known for item in relation.evidence):
                raise ValueError("spatial relation references an unknown photo")
        return self
