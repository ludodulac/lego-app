"""Pydantic contracts for ArchitecturalScene v0.2."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import (
    Appearance,
    Facade,
    OpeningType,
    Position3D,
    RidgeDirection,
    RoofType,
    SourceInfo,
    WindowStyle,
)


class Evidence(BaseModel):
    photo_index: int = Field(ge=1)
    observation: str = Field(min_length=1)


class PropertyValue(BaseModel):
    value: float
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)


class SceneVolume(BaseModel):
    id: str
    position: Position3D
    width: PropertyValue
    depth: PropertyValue
    height: PropertyValue
    floors: int = Field(ge=1, le=10)
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)


class SceneOpening(BaseModel):
    id: str
    type: OpeningType
    volume_id: str
    facade: Facade
    offset_horizontal: float = Field(ge=0)
    offset_vertical: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)
    local_grade_clearance: float | None = None
    window_style: WindowStyle | None = None
    has_sill: bool | None = None
    has_decorative_surround: bool | None = None

    @model_validator(mode="after")
    def validate_window_metadata(self) -> "SceneOpening":
        if self.type is not OpeningType.WINDOW:
            fields = (self.window_style, self.has_sill, self.has_decorative_surround)
            if any(value is not None for value in fields):
                raise ValueError("window metadata may only be set for window openings")
        return self


class SceneRoof(BaseModel):
    id: str
    volume_id: str
    type: RoofType
    overhang: float = Field(ge=0)
    ridge_direction: RidgeDirection | None = None
    pitch_degrees: float | None = None
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_roof(self) -> "SceneRoof":
        if self.type is RoofType.GABLE:
            if self.ridge_direction is None or self.pitch_degrees is None:
                raise ValueError("gable roof requires ridge_direction and pitch_degrees")
            if not 0 < self.pitch_degrees < 90:
                raise ValueError("gable roof pitch_degrees must be > 0 and < 90")
        elif self.ridge_direction is not None or self.pitch_degrees is not None:
            raise ValueError("flat roof must not define gable-only fields")
        return self


class GradeProfile(BaseModel):
    facade: Facade
    start_elevation: float
    end_elevation: float
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)


class Terrain(BaseModel):
    kind: Literal["facade_grade_profiles"] = "facade_grade_profiles"
    profiles: list[GradeProfile] = Field(default_factory=list)


class Chimney(BaseModel):
    id: str
    position: Position3D
    width: float = Field(gt=0)
    depth: float = Field(gt=0)
    height: float = Field(gt=0)
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)


class SupportPost(BaseModel):
    id: str
    position: Position3D
    width: float = Field(gt=0)
    depth: float = Field(gt=0)
    height: float = Field(gt=0)
    source: SourceInfo


class Platform(BaseModel):
    id: str
    position: Position3D
    width: float = Field(gt=0)
    depth: float = Field(gt=0)
    thickness: float = Field(gt=0)
    supports: list[SupportPost] = Field(default_factory=list)
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)


class StairRun(BaseModel):
    id: str
    start: Position3D
    end: Position3D
    width: float = Field(gt=0)
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)


class EquipmentType(str, Enum):
    UTILITY_BOX = "utility_box"
    PIPE = "pipe"
    GUTTER = "gutter"
    DOWNSPOUT = "downspout"
    VENT = "vent"
    ANTENNA = "antenna"
    TEMPORARY_OBJECT = "temporary_object"


class FacadeEquipment(BaseModel):
    id: str
    type: EquipmentType
    facade: Facade | None = None
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)


class VisibilityState(str, Enum):
    VISIBLE = "visible"
    OCCLUDED = "occluded"
    UNKNOWN = "unknown"


class VisibilitySpan(BaseModel):
    from_offset: float = Field(ge=0, alias="from")
    to_offset: float = Field(gt=0, alias="to")
    state: VisibilityState
    by: str | None = None

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_order(self) -> "VisibilitySpan":
        if self.to_offset <= self.from_offset:
            raise ValueError("visibility span to must be greater than from")
        return self


class FacadeVisibility(BaseModel):
    facade: Facade
    spans: list[VisibilitySpan] = Field(default_factory=list)


class ArchitecturalScene(BaseModel):
    schema_version: Literal["0.2"]
    id: str
    name: str
    units: Literal["m"] = "m"
    volumes: list[SceneVolume] = Field(min_length=1)
    openings: list[SceneOpening] = Field(default_factory=list)
    roofs: list[SceneRoof] = Field(default_factory=list)
    terrain: Terrain | None = None
    chimneys: list[Chimney] = Field(default_factory=list)
    platforms: list[Platform] = Field(default_factory=list)
    stairs: list[StairRun] = Field(default_factory=list)
    equipment: list[FacadeEquipment] = Field(default_factory=list)
    visibility: list[FacadeVisibility] = Field(default_factory=list)
    appearance: Appearance
    notes: str | None = None

    @model_validator(mode="after")
    def validate_scene(self) -> "ArchitecturalScene":
        ids = [item.id for item in [*self.volumes, *self.openings, *self.roofs, *self.chimneys, *self.platforms, *self.stairs, *self.equipment]]
        for platform in self.platforms:
            ids.extend(post.id for post in platform.supports)
        if len(ids) != len(set(ids)):
            raise ValueError("scene object IDs must be globally unique")

        volumes = {volume.id: volume for volume in self.volumes}
        for opening in self.openings:
            if opening.volume_id not in volumes:
                raise ValueError(f"opening {opening.id!r} references unknown volume")
        for roof in self.roofs:
            if roof.volume_id not in volumes:
                raise ValueError(f"roof {roof.id!r} references unknown volume")

        visibility_by_facade = {entry.facade: entry for entry in self.visibility}
        for opening in self.openings:
            entry = visibility_by_facade.get(opening.facade)
            if entry is None:
                continue
            center = opening.offset_horizontal + opening.width / 2
            for span in entry.spans:
                if span.from_offset <= center <= span.to_offset and span.state is not VisibilityState.VISIBLE:
                    raise ValueError(f"opening {opening.id!r} is centered in non-visible facade span")
        return self
