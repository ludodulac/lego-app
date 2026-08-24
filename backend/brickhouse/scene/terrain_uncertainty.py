"""Terrain contract that preserves a known grade even when its metric amplitude is unknown."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from brickhouse.building import Facade, SourceInfo

from .models import Evidence


class GradeProfile(BaseModel):
    facade: Facade
    start_elevation: float | None = None
    end_elevation: float | None = None
    outward_extent: float | None = Field(default=None, gt=0)
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)


class Terrain(BaseModel):
    kind: Literal["facade_grade_profiles"] = "facade_grade_profiles"
    profiles: list[GradeProfile] = Field(default_factory=list)
