"""Contracts for photo-derived architectural proposals."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, model_validator

from brickhouse.building.models import BuildingModel
from .compatibility import M0Compatibility


class ClarificationQuestion(BaseModel):
    id: str
    question: str
    reason: str
    importance: Literal["required", "recommended"]


class ProportionEvidence(BaseModel):
    """One explicit piece of evidence used to recover real architectural proportions."""
    facade: Literal["front", "rear", "left", "right", "global"]
    observation: str
    method: Literal[
        "perspective_corrected_ratio",
        "cross_view_consistency",
        "known_scale_anchor",
        "architectural_alignment",
        "uncertain",
    ]
    confidence: float = Field(ge=0.0, le=1.0)


class VisionNormalizedImagePoint(BaseModel):
    """Provider proposal in the existing per-axis normalized image coordinate space."""

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)


VisionLandmarkObservationStatus = Literal["PROPOSED", "AMBIGUOUS", "REJECTED"]
VisionLandmarkIdentityStatus = Literal["PROPOSED", "AMBIGUOUS", "REJECTED"]


class VisionLandmarkObservationProposal(BaseModel):
    """One provider-proposed occurrence of a named physical architectural point."""

    photo_index: int = Field(ge=1)
    point: VisionNormalizedImagePoint
    confidence: float = Field(ge=0.0, le=1.0)
    status: VisionLandmarkObservationStatus = "PROPOSED"
    ambiguity_reason: str | None = None
    survey_observation_id: str | None = None
    survey_object_id: str | None = None
    provider: str = Field(default="vision_provider", min_length=1)
    provider_model: str | None = None
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_ambiguity(self) -> "VisionLandmarkObservationProposal":
        if self.status in {"AMBIGUOUS", "REJECTED"} and not self.ambiguity_reason:
            raise ValueError("ambiguous or rejected landmark observations require an ambiguity_reason")
        return self


class VisionArchitecturalLandmarkProposal(BaseModel):
    """Provider hypothesis that listed image points denote one physical architectural landmark.

    Identity remains a proposal. It becomes an ArchitecturalLandmarkTrack only after
    provenance and local geometric validation at the photo-landmark boundary.
    """

    physical_landmark_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    observations: list[VisionLandmarkObservationProposal] = Field(min_length=2)
    confidence: float = Field(ge=0.0, le=1.0)
    identity_status: VisionLandmarkIdentityStatus = "PROPOSED"
    ambiguity_reason: str | None = None
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_cross_view_identity(self) -> "VisionArchitecturalLandmarkProposal":
        photos = [item.photo_index for item in self.observations]
        if len(photos) != len(set(photos)):
            raise ValueError("a vision landmark proposal may contain at most one occurrence per photo")
        if self.identity_status in {"AMBIGUOUS", "REJECTED"} and not self.ambiguity_reason:
            raise ValueError("ambiguous or rejected physical landmark identities require an ambiguity_reason")
        return self


class VisionPhotoEvidenceCandidate(BaseModel):
    """Candidate extra photo evidence for an already-known Survey observation.

    This does not mutate or extend an accepted Survey. It records the provider claim
    separately so a later validation step can accept or reject that additional view.
    """

    survey_observation_id: str = Field(min_length=1)
    photo_index: int = Field(ge=1)
    statement: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    status: Literal["PROPOSED", "AMBIGUOUS", "REJECTED"] = "PROPOSED"
    ambiguity_reason: str | None = None
    provider: str = Field(default="vision_provider", min_length=1)
    provider_model: str | None = None

    @model_validator(mode="after")
    def validate_candidate(self) -> "VisionPhotoEvidenceCandidate":
        if self.status in {"AMBIGUOUS", "REJECTED"} and not self.ambiguity_reason:
            raise ValueError("ambiguous or rejected photo evidence candidates require an ambiguity_reason")
        return self


class PhotoAnalysisResult(BaseModel):
    # 0.2 adds compatibility metadata; 0.3 adds explicit proportion/scale evidence.
    # 0.4 adds a strictly additive physical-landmark/evidence-candidate sidecar.
    # Older provider/stored payloads remain readable and are enriched by live analysis.
    schema_version: Literal["0.1", "0.2", "0.3", "0.4"] = "0.4"
    building: BuildingModel
    questions: list[ClarificationQuestion] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_confirmation: bool
    m0_compatibility: M0Compatibility | None = None
    scale_basis: str | None = None
    proportion_evidence: list[ProportionEvidence] = Field(default_factory=list)
    landmark_proposals: list[VisionArchitecturalLandmarkProposal] = Field(default_factory=list)
    photo_evidence_candidates: list[VisionPhotoEvidenceCandidate] = Field(default_factory=list)
