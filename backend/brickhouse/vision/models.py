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


class VisionImagePoint(BaseModel):
    """Provider-proposed point in original image coordinates normalized by width/height."""

    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)


VisionLandmarkStatus = Literal["PROPOSED", "AMBIGUOUS", "REJECTED"]


class VisionLandmarkObservationProposal(BaseModel):
    """One provider proposal for a named physical landmark in one supplied photo."""

    photo_index: int = Field(ge=1)
    point: VisionImagePoint
    survey_observation_id: str | None = None
    survey_object_hint: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    status: VisionLandmarkStatus = "PROPOSED"
    statement: str = Field(min_length=1)
    provider: str = Field(min_length=1)


class VisionLandmarkProposal(BaseModel):
    """Cross-view physical-identity proposal; it is evidence, not geometric truth."""

    physical_landmark_id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    observations: list[VisionLandmarkObservationProposal] = Field(min_length=2, max_length=12)
    identity_confidence: float = Field(ge=0.0, le=1.0)
    status: VisionLandmarkStatus = "PROPOSED"
    ambiguity_reason: str | None = None

    @model_validator(mode="after")
    def validate_cross_view_identity(self) -> "VisionLandmarkProposal":
        photos = [item.photo_index for item in self.observations]
        if len(photos) != len(set(photos)):
            raise ValueError("vision landmark proposal may contain at most one observation per photo")
        if self.status != "PROPOSED" and not self.ambiguity_reason:
            raise ValueError("ambiguous/rejected landmark proposals require an explicit reason")
        return self


class PhotoAnalysisResult(BaseModel):
    # 0.2 adds compatibility metadata; 0.3 adds explicit proportion/scale evidence;
    # 0.4 adds bounded cross-view landmark proposals. Older payloads stay readable.
    schema_version: Literal["0.1", "0.2", "0.3", "0.4"] = "0.4"
    building: BuildingModel
    questions: list[ClarificationQuestion] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_confirmation: bool
    m0_compatibility: M0Compatibility | None = None
    scale_basis: str | None = None
    proportion_evidence: list[ProportionEvidence] = Field(default_factory=list)
    landmark_proposals: list[VisionLandmarkProposal] = Field(default_factory=list, max_length=15)
