"""Contracts for photo-derived architectural proposals."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel
from .compatibility import M0Compatibility


class ClarificationQuestion(BaseModel):
    id: str
    question: str
    reason: str
    importance: Literal["required", "recommended"]


class PhotoAnalysisResult(BaseModel):
    schema_version: Literal["0.2"] = "0.2"
    building: BuildingModel
    questions: list[ClarificationQuestion] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    needs_confirmation: bool
    m0_compatibility: M0Compatibility | None = None
