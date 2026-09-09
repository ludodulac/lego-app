"""Provenance links from metric Scene stair runs to one semantic Survey stair system.

The link is an append-only Scene sidecar. It lets metric segmentation happen in
Scene without fabricating separate Survey observations for every run.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind


class SceneStairSystemLink(BaseModel):
    id: str = Field(min_length=1)
    stair_run_id: str = Field(min_length=1)
    survey_stair_system_id: str = Field(min_length=1)
    source: SourceInfo
    statement: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_source(self) -> "SceneStairSystemLink":
        if self.source.kind is SourceKind.GENERATED_DEFAULT:
            raise ValueError("stair-system provenance link cannot be generated_default")
        return self
