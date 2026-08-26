"""Pydantic contracts for ArchitecturalScene v0.2."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import Appearance, Facade, OpeningType, Position3D, RidgeDirection, SourceInfo, WindowStyle

EPSILON = 1e-9
CONNECTIVITY_TOLERANCE_M = 0.12


class Evidence(BaseModel):
    photo_index: int = Field(ge=1)
    observation: str = Field(min_length=1)


class PropertyValue(BaseModel):
    # ArchitecturalScene is allowed to preserve an explicitly unknown metric.
    # Downstream projection/build gates decide whether a concrete value is
    # required; the understanding layer must not fabricate one merely to parse.
    value: float | None = Field(default=None, gt=0)
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
    def validate_window_metadata(self):
        if self.type is not OpeningType.WINDOW and any(
            value is not None for value in (self.window_style, self.has_sill, self.has_decorative_surround)
        ):
            raise ValueError("window metadata may only be set for window openings")
        return self


class SceneRoofType(str, Enum):
    """Architectural roof types preserved even when the LEGO backend cannot render them yet."""

    FLAT = "flat"
    GABLE = "gable"
    HIP = "hip"
    SHED = "shed"
    MANSARD = "mansard"
    GAMBREL = "gambrel"
    BUTTERFLY = "butterfly"
    OTHER = "other"


class RoofPitchRange(BaseModel):
    """Evidence-backed interval when photos constrain pitch without proving one exact angle."""

    min_degrees: float = Field(gt=0, lt=90)
    max_degrees: float = Field(gt=0, lt=90)
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_bounds(self):
        if self.max_degrees <= self.min_degrees:
            raise ValueError("roof pitch range max_degrees must be greater than min_degrees")
        return self


class SceneRoof(BaseModel):
    id: str
    volume_id: str
    type: SceneRoofType
    overhang: float = Field(ge=0)
    ridge_direction: RidgeDirection | None = None
    # For a mono-pitch roof this is the facade toward which the roof plane falls.
    # It is deliberately nullable in ArchitecturalScene: visual evidence can prove
    # roof existence/type without proving orientation or a numeric pitch.
    down_slope_direction: Facade | None = None
    pitch_degrees: float | None = None
    # A range records what the evidence bounds without pretending that one angle
    # inside that interval has been observed. BuildingModel still requires an exact
    # construction metric and must never silently choose a midpoint/default.
    pitch_range_degrees: RoofPitchRange | None = None
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_roof(self):
        if self.pitch_degrees is not None and not 0 < self.pitch_degrees < 90:
            raise ValueError("roof pitch_degrees must be > 0 and < 90 when provided")
        if self.pitch_degrees is not None and self.pitch_range_degrees is not None:
            raise ValueError("roof must not define both exact pitch_degrees and pitch_range_degrees")
        # ArchitecturalScene is an understanding layer, not a construction
        # solver. A pitched roof can be visually certain while orientation or
        # pitch remain unknown. Keep those fields nullable here; projection/build
        # gates decide whether enough metric information exists to construct it.
        if self.type is SceneRoofType.FLAT:
            if (
                self.ridge_direction is not None
                or self.down_slope_direction is not None
                or self.pitch_degrees is not None
                or self.pitch_range_degrees is not None
            ):
                raise ValueError("flat roof must not define pitched-roof fields")
        elif self.type is SceneRoofType.SHED:
            if self.ridge_direction is not None:
                raise ValueError("shed roof must not define ridge_direction")
        elif self.down_slope_direction is not None:
            raise ValueError("down_slope_direction may only be defined for shed roofs")
        return self


class GradeProfile(BaseModel):
    facade: Facade
    start_elevation: float
    end_elevation: float
    outward_extent: float | None = Field(default=None, gt=0)
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


class DeckBoardDirection(str, Enum):
    X = "x"
    Y = "y"
    UNKNOWN = "unknown"


class EdgeTreatment(str, Enum):
    NONE = "none"
    OPEN_RAILING = "open_railing"
    SOLID_PARAPET = "solid_parapet"
    WALL_ATTACHED = "wall_attached"
    ACCESS_OPENING = "access_opening"
    UNKNOWN = "unknown"


class EdgeAccessSpan(BaseModel):
    from_offset: float = Field(ge=0, alias="from")
    to_offset: float = Field(gt=0, alias="to")
    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def validate_order(self):
        if self.to_offset <= self.from_offset:
            raise ValueError("edge access span to must be greater than from")
        return self


class PlatformEdge(BaseModel):
    treatment: EdgeTreatment = EdgeTreatment.UNKNOWN
    access_spans: list[EdgeAccessSpan] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_access(self):
        ordered = sorted(self.access_spans, key=lambda span: span.from_offset)
        for first, second in zip(ordered, ordered[1:]):
            if second.from_offset < first.to_offset - EPSILON:
                raise ValueError("platform edge access spans must not overlap")
        return self


class PlatformEdges(BaseModel):
    x_min: PlatformEdge = Field(default_factory=PlatformEdge)
    x_max: PlatformEdge = Field(default_factory=PlatformEdge)
    y_min: PlatformEdge = Field(default_factory=PlatformEdge)
    y_max: PlatformEdge = Field(default_factory=PlatformEdge)


class SupportPost(BaseModel):
    id: str
    position: Position3D
    width: float = Field(gt=0)
    depth: float = Field(gt=0)
    height: float = Field(gt=0)
    source: SourceInfo


class Platform(BaseModel):
    id: str
    # Multi-volume scenes must be able to say which architectural volume owns
    # an attached terrace/balcony. Legacy null means the primary first volume.
    host_volume_id: str | None = None
    position: Position3D
    width: float = Field(gt=0)
    depth: float = Field(gt=0)
    thickness: float = Field(gt=0)
    supports: list[SupportPost] = Field(default_factory=list)
    material: ExteriorMaterial | None = None
    deck_board_direction: DeckBoardDirection | None = None
    edge_treatment: EdgeTreatment | None = None
    edges: PlatformEdges | None = None
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_edge_spans(self):
        if self.edges is None:
            return self
        for name in ("x_min", "x_max"):
            if any(span.to_offset > self.depth + EPSILON for span in getattr(self.edges, name).access_spans):
                raise ValueError(f"platform {self.id!r} access span on {name} exceeds depth")
        for name in ("y_min", "y_max"):
            if any(span.to_offset > self.width + EPSILON for span in getattr(self.edges, name).access_spans):
                raise ValueError(f"platform {self.id!r} access span on {name} exceeds width")
        return self


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
    def validate_order(self):
        if self.to_offset <= self.from_offset:
            raise ValueError("visibility span to must be greater than from")
        return self


class FacadeVisibility(BaseModel):
    volume_id: str | None = None
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
    def validate_scene(self):
        self._validate_ids_and_references()
        self._validate_opening_geometry()
        self._validate_visibility()
        self._validate_external_connectivity()
        return self

    def _validate_ids_and_references(self):
        ids = [
            item.id
            for item in [
                *self.volumes,
                *self.openings,
                *self.roofs,
                *self.chimneys,
                *self.platforms,
                *self.stairs,
                *self.equipment,
            ]
        ]
        for platform in self.platforms:
            ids.extend(support.id for support in platform.supports)
        if len(ids) != len(set(ids)):
            raise ValueError("scene object IDs must be globally unique")

        volumes = {volume.id: volume for volume in self.volumes}
        roof_ids = set()
        for opening in self.openings:
            if opening.volume_id not in volumes:
                raise ValueError(f"opening {opening.id!r} references unknown volume")
        for roof in self.roofs:
            if roof.volume_id not in volumes:
                raise ValueError(f"roof {roof.id!r} references unknown volume")
            if roof.volume_id in roof_ids:
                raise ValueError("at most one roof may reference a scene volume in v0.2")
            roof_ids.add(roof.volume_id)
        for platform in self.platforms:
            if platform.host_volume_id is not None and platform.host_volume_id not in volumes:
                raise ValueError(f"platform {platform.id!r} references unknown host volume {platform.host_volume_id!r}")
        for entry in self.visibility:
            if entry.volume_id is not None and entry.volume_id not in volumes:
                raise ValueError(f"visibility on {entry.facade.value} references unknown volume {entry.volume_id!r}")

    def _validate_opening_geometry(self):
        volumes = {volume.id: volume for volume in self.volumes}
        for opening in self.openings:
            volume = volumes[opening.volume_id]
            span = volume.width.value if opening.facade in {Facade.FRONT, Facade.REAR} else volume.depth.value
            if span is not None and opening.offset_horizontal + opening.width > span + EPSILON:
                raise ValueError(f"opening {opening.id!r} extends past facade horizontally")
            if volume.height.value is not None and opening.offset_vertical + opening.height > volume.height.value + EPSILON:
                raise ValueError(f"opening {opening.id!r} extends above volume")
        for index, first in enumerate(self.openings):
            for second in self.openings[index + 1 :]:
                if (
                    first.volume_id == second.volume_id
                    and first.facade is second.facade
                    and self._openings_overlap(first, second)
                ):
                    raise ValueError(f"openings {first.id!r} and {second.id!r} overlap")

    @staticmethod
    def _openings_overlap(first, second):
        return (
            first.offset_horizontal < second.offset_horizontal + second.width - EPSILON
            and second.offset_horizontal < first.offset_horizontal + first.width - EPSILON
            and first.offset_vertical < second.offset_vertical + second.height - EPSILON
            and second.offset_vertical < first.offset_vertical + first.height - EPSILON
        )

    def _validate_visibility(self):
        volumes = {volume.id: volume for volume in self.volumes}
        primary_volume_id = self.volumes[0].id

        def scope(entry):
            return entry.volume_id or primary_volume_id

        keys = [(scope(entry), entry.facade) for entry in self.visibility]
        if len(keys) != len(set(keys)):
            raise ValueError("at most one visibility entry may be defined per volume/facade")

        by_scope_facade = {(scope(entry), entry.facade): entry for entry in self.visibility}
        for entry in self.visibility:
            volume_id = scope(entry)
            volume = volumes[volume_id]
            span = volume.width.value if entry.facade in {Facade.FRONT, Facade.REAR} else volume.depth.value
            if span is not None and any(item.to_offset > span + EPSILON for item in entry.spans):
                raise ValueError(
                    f"visibility span on volume {volume_id!r} facade {entry.facade.value} extends past facade"
                )
            ordered = sorted(entry.spans, key=lambda item: item.from_offset)
            for previous, current in zip(ordered, ordered[1:]):
                if current.from_offset < previous.to_offset - EPSILON:
                    raise ValueError(
                        f"visibility spans overlap on volume {volume_id!r} facade {entry.facade.value}"
                    )

        for opening in self.openings:
            entry = by_scope_facade.get((opening.volume_id, opening.facade))
            if entry:
                for span in entry.spans:
                    if (
                        opening.offset_horizontal < span.to_offset - EPSILON
                        and span.from_offset < opening.offset_horizontal + opening.width - EPSILON
                        and span.state is not VisibilityState.VISIBLE
                    ):
                        raise ValueError(f"opening {opening.id!r} intersects non-visible facade span")

    @staticmethod
    def _point_on_platform(point, platform):
        return (
            platform.position.x - CONNECTIVITY_TOLERANCE_M <= point.x <= platform.position.x + platform.width + CONNECTIVITY_TOLERANCE_M
            and platform.position.y - CONNECTIVITY_TOLERANCE_M <= point.y <= platform.position.y + platform.depth + CONNECTIVITY_TOLERANCE_M
            and abs(point.z - platform.position.z) <= CONNECTIVITY_TOLERANCE_M
        )

    @staticmethod
    def _point_on_volume_boundary(point, volume):
        if any(value is None for value in (volume.width.value, volume.depth.value, volume.height.value)):
            return False
        x0, x1 = volume.position.x, volume.position.x + volume.width.value
        y0, y1 = volume.position.y, volume.position.y + volume.depth.value
        z0, z1 = volume.position.z, volume.position.z + volume.height.value
        return (
            x0 - CONNECTIVITY_TOLERANCE_M <= point.x <= x1 + CONNECTIVITY_TOLERANCE_M
            and y0 - CONNECTIVITY_TOLERANCE_M <= point.y <= y1 + CONNECTIVITY_TOLERANCE_M
            and min(abs(point.x - x0), abs(point.x - x1), abs(point.y - y0), abs(point.y - y1)) <= CONNECTIVITY_TOLERANCE_M
            and z0 - CONNECTIVITY_TOLERANCE_M <= point.z <= z1 + CONNECTIVITY_TOLERANCE_M
        )

    @staticmethod
    def _platform_touches_volume(platform, volume):
        if volume.width.value is None or volume.depth.value is None:
            return False
        px0, px1 = platform.position.x, platform.position.x + platform.width
        py0, py1 = platform.position.y, platform.position.y + platform.depth
        vx0, vx1 = volume.position.x, volume.position.x + volume.width.value
        vy0, vy1 = volume.position.y, volume.position.y + volume.depth.value
        x_overlap = min(px1, vx1) >= max(px0, vx0) - CONNECTIVITY_TOLERANCE_M
        y_overlap = min(py1, vy1) >= max(py0, vy0) - CONNECTIVITY_TOLERANCE_M
        return (
            min(abs(px0 - vx1), abs(px1 - vx0)) <= CONNECTIVITY_TOLERANCE_M and y_overlap
        ) or (
            min(abs(py0 - vy1), abs(py1 - vy0)) <= CONNECTIVITY_TOLERANCE_M and x_overlap
        )

    def _validate_external_connectivity(self):
        if not self.platforms and not self.stairs:
            return
        for platform in self.platforms:
            if not any(self._platform_touches_volume(platform, volume) for volume in self.volumes) and not any(
                self._point_on_platform(stair.start, platform) or self._point_on_platform(stair.end, platform)
                for stair in self.stairs
            ):
                raise ValueError(f"platform {platform.id!r} is disconnected from both building and stairs")
        for stair in self.stairs:
            for name, point in (("start", stair.start), ("end", stair.end)):
                if not (
                    any(self._point_on_platform(point, platform) for platform in self.platforms)
                    or any(self._point_on_volume_boundary(point, volume) for volume in self.volumes)
                    or point.z <= CONNECTIVITY_TOLERANCE_M
                ):
                    raise ValueError(f"stair {stair.id!r} {name} does not connect to ground, a platform, or the building")