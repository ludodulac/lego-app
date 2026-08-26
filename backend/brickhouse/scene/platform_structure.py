"""Non-metric platform structure observations for ArchitecturalScene.

This contract records visibly present deck/terrace components before their count or
coordinates are metrically resolved. It deliberately contains no position fields:
resolved support-post geometry continues to live in ``SupportPost``.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from brickhouse.building import SourceInfo

from .models import Evidence


class PlatformStructureKind(str, Enum):
    VERTICAL_POST = "vertical_post"
    DIAGONAL_BRACE = "diagonal_brace"
    GUARDRAIL = "guardrail"


class PlatformStructureObservation(BaseModel):
    id: str = Field(min_length=1)
    platform_id: str = Field(min_length=1)
    kind: PlatformStructureKind
    statement: str = Field(min_length=1)
    count: int | None = Field(default=None, ge=1)
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)
