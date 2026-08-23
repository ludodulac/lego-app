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

EPSILON = 1e-9
CONNECTIVITY_TOLERANCE_M = 0.12


class Evidence(BaseModel):
    photo_index: int = Field(ge=1)
    observation: str = Field(min_length=1)


class PropertyValue(BaseModel):
    value: float = Field(gt=0)
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


class ExteriorMaterial(str, Enum):
    TIMBER = "timber"
    CONCRETE = "concrete"
    MASONRY = "masonry"
    STONE = "stone"
    METAL = "metal"
    COMPOSITE = "composite"
    UNKNOWN = "unknown"


class EdgeTreatment(str, Enum):
    NONE = "none"
    OPEN_RAILING = "open_railing"
    SOLID_PARAPET = "solid_parapet"
    UNKNOWN = "unknown"


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
    material: ExteriorMaterial | None = None
    edge_treatment: EdgeTreatment | None = None
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)


class StairRun(BaseModel):
    id: str
    start: Position3D
    end: Position3D
    width: float = Field(gt=0)
    material: ExteriorMaterial | None = None
    left_edge: EdgeTreatment | None = None
    right_edge: EdgeTreatment | None = None
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
        self._validate_ids_and_references()
        self._validate_opening_geometry()
        self._validate_visibility()
        self._validate_external_connectivity()
        return self

    def _validate_ids_and_references(self) -> None:
        ids = [item.id for item in [*self.volumes, *self.openings, *self.roofs, *self.chimneys, *self.platforms, *self.stairs, *self.equipment]]
        for platform in self.platforms:
            ids.extend(post.id for post in platform.supports)
        if len(ids) != len(set(ids)):
            raise ValueError("scene object IDs must be globally unique")

        volumes = {volume.id: volume for volume in self.volumes}
        for opening in self.openings:
            if opening.volume_id not in volumes:
                raise ValueError(f"opening {opening.id!r} references unknown volume")
        roof_volume_ids: set[str] = set()
        for roof in self.roofs:
            if roof.volume_id not in volumes:
                raise ValueError(f"roof {roof.id!r} references unknown volume")
            if roof.volume_id in roof_volume_ids:
                raise ValueError("at most one roof may reference a scene volume in v0.2")
            roof_volume_ids.add(roof.volume_id)

    def _validate_opening_geometry(self) -> None:
        volumes = {volume.id: volume for volume in self.volumes}
        for opening in self.openings:
            volume = volumes[opening.volume_id]
            facade_span = volume.width.value if opening.facade in {Facade.FRONT, Facade.REAR} else volume.depth.value
            if opening.offset_horizontal + opening.width > facade_span + EPSILON:
                raise ValueError(f"opening {opening.id!r} extends past facade horizontally")
            if opening.offset_vertical + opening.height > volume.height.value + EPSILON:
                raise ValueError(f"opening {opening.id!r} extends above volume")

        for index, first in enumerate(self.openings):
            for second in self.openings[index + 1 :]:
                if first.volume_id != second.volume_id or first.facade is not second.facade:
                    continue
                if self._openings_overlap(first, second):
                    raise ValueError(f"openings {first.id!r} and {second.id!r} overlap")

    @staticmethod
    def _openings_overlap(first: SceneOpening, second: SceneOpening) -> bool:
        return (
            first.offset_horizontal < second.offset_horizontal + second.width - EPSILON
            and second.offset_horizontal < first.offset_horizontal + first.width - EPSILON
            and first.offset_vertical < second.offset_vertical + second.height - EPSILON
            and second.offset_vertical < first.offset_vertical + first.height - EPSILON
        )

    def _validate_visibility(self) -> None:
        if len({entry.facade for entry in self.visibility}) != len(self.visibility):
            raise ValueError("at most one visibility entry may be defined per facade")

        visibility_by_facade = {entry.facade: entry for entry in self.visibility}
        for entry in self.visibility:
            if len(self.volumes) == 1:
                volume = self.volumes[0]
                facade_span = volume.width.value if entry.facade in {Facade.FRONT, Facade.REAR} else volume.depth.value
                for span in entry.spans:
                    if span.to_offset > facade_span + EPSILON:
                        raise ValueError(f"visibility span on {entry.facade.value} extends past facade")
            ordered = sorted(entry.spans, key=lambda span: span.from_offset)
            for previous, current in zip(ordered, ordered[1:]):
                if current.from_offset < previous.to_offset - EPSILON:
                    raise ValueError(f"visibility spans overlap on facade {entry.facade.value}")

        for opening in self.openings:
            entry = visibility_by_facade.get(opening.facade)
            if entry is None:
                continue
            opening_from = opening.offset_horizontal
            opening_to = opening.offset_horizontal + opening.width
            for span in entry.spans:
                intersects = opening_from < span.to_offset - EPSILON and span.from_offset < opening_to - EPSILON
                if intersects and span.state is not VisibilityState.VISIBLE:
                    raise ValueError(f"opening {opening.id!r} intersects non-visible facade span")

    @staticmethod
    def _point_on_platform(point: Position3D, platform: Platform) -> bool:
        return (
            platform.position.x - CONNECTIVITY_TOLERANCE_M <= point.x <= platform.position.x + platform.width + CONNECTIVITY_TOLERANCE_M
            and platform.position.y - CONNECTIVITY_TOLERANCE_M <= point.y <= platform.position.y + platform.depth + CONNECTIVITY_TOLERANCE_M
            and abs(point.z - platform.position.z) <= CONNECTIVITY_TOLERANCE_M
        )

    @staticmethod
    def _point_on_volume_boundary(point: Position3D, volume: SceneVolume) -> bool:
        x0, x1 = volume.position.x, volume.position.x + volume.width.value
        y0, y1 = volume.position.y, volume.position.y + volume.depth.value
        z0, z1 = volume.position.z, volume.position.z + volume.height.value
        inside_xy = x0 - CONNECTIVITY_TOLERANCE_M <= point.x <= x1 + CONNECTIVITY_TOLERANCE_M and y0 - CONNECTIVITY_TOLERANCE_M <= point.y <= y1 + CONNECTIVITY_TOLERANCE_M
        on_edge = min(abs(point.x - x0), abs(point.x - x1), abs(point.y - y0), abs(point.y - y1)) <= CONNECTIVITY_TOLERANCE_M
        return inside_xy and on_edge and z0 - CONNECTIVITY_TOLERANCE_M <= point.z <= z1 + CONNECTIVITY_TOLERANCE_M

    @staticmethod
    def _platform_touches_volume(platform: Platform, volume: SceneVolume) -> bool:
        px0, px1 = platform.position.x, platform.position.x + platform.width
        py0, py1 = platform.position.y, platform.position.y + platform.depth
        vx0, vx1 = volume.position.x, volume.position.x + volume.width.value
        vy0, vy1 = volume.position.y, volume.position.y + volume.depth.value
        x_overlap = min(px1, vx1) >= max(px0, vx0) - CONNECTIVITY_TOLERANCE_M
        y_overlap = min(py1, vy1) >= max(py0, vy0) - CONNECTIVITY_TOLERANCE_M
        x_touch = min(abs(px0 - vx1), abs(px1 - vx0)) <= CONNECTIVITY_TOLERANCE_M and y_overlap
        y_touch = min(abs(py0 - vy1), abs(py1 - vy0)) <= CONNECTIVITY_TOLERANCE_M and x_overlap
        return x_touch or y_touch

    def _validate_external_connectivity(self) -> None:
        if not self.platforms and not self.stairs:
            return
        for platform in self.platforms:
            touches_building = any(self._platform_touches_volume(platform, volume) for volume in self.volumes)
            touches_stair = any(self._point_on_platform(stair.start, platform) or self._point_on_platform(stair.end, platform) for stair in self.stairs)
            if not touches_building and not touches_stair:
                raise ValueError(f"platform {platform.id!r} is disconnected from both building and stairs")
        for stair in self.stairs:
            for endpoint_name, endpoint in (("start", stair.start), ("end", stair.end)):
                connects = any(self._point_on_platform(endpoint, platform) for platform in self.platforms) or any(self._point_on_volume_boundary(endpoint, volume) for volume in self.volumes)
                if endpoint.z <= CONNECTIVITY_TOLERANCE_M:
                    connects = True
                if not connects:
                    raise ValueError(f"stair {stair.id!r} {endpoint_name} does not connect to ground, a platform, or the building")
