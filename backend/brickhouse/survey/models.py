"""Architectural survey contracts: observation before reconstruction."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import Facade, SourceInfo


class Certainty(str, Enum):
    CERTAIN = "certain"
    PLAUSIBLE = "plausible"
    UNPROVEN = "unproven"


class ObservationKind(str, Enum):
    BUILDING_BOUNDARY = "building_boundary"
    TERRAIN = "terrain"
    MATERIAL = "material"
    WEATHERING = "weathering"
    OPENING = "opening"
    ROOF = "roof"
    CHIMNEY = "chimney"
    EQUIPMENT = "equipment"
    VOLUME = "volume"
    PLATFORM = "platform"
    STAIR = "stair"
    OCCLUSION = "occlusion"
    CONTEXT = "context"


class NormalizedImageRegion(BaseModel):
    """Optional evidence box in image coordinates, normalized to 0..1."""

    x0: float = Field(ge=0, le=1)
    y0: float = Field(ge=0, le=1)
    x1: float = Field(ge=0, le=1)
    y1: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_order(self) -> "NormalizedImageRegion":
        if self.x1 <= self.x0 or self.y1 <= self.y0:
            raise ValueError("image region must have positive area")
        return self


class PhotoEvidence(BaseModel):
    photo_index: int = Field(ge=1)
    observation: str = Field(min_length=1)
    region: NormalizedImageRegion | None = None


class CanonicalFrame(BaseModel):
    """Building-centric orientation independent of camera mirroring.

    x increases from the left edge to the right edge when an observer stands
    outside and looks straight at the canonical front facade. y increases from
    front to rear, z from low to high.
    """

    front_facade: Literal["front"] = "front"
    x_direction: Literal["front_view_left_to_right"] = "front_view_left_to_right"
    y_direction: Literal["front_to_rear"] = "front_to_rear"
    z_direction: Literal["bottom_to_top"] = "bottom_to_top"


class PhotoView(BaseModel):
    photo_index: int = Field(ge=1)
    facade: Facade
    description: str = Field(min_length=1)
    source: SourceInfo
    image_left_maps_to_facade_offset: Literal["low", "high"] = "low"


class KnownMeasurement(BaseModel):
    """Exact user-supplied metric anchors that must survive every AI handoff."""

    kind: Literal["front_width"]
    value: float = Field(gt=0)
    units: Literal["m"] = "m"
    source: SourceInfo


class SurfaceAppearance(BaseModel):
    base_material: str = Field(min_length=1)
    nominal_color: str = Field(min_length=1)
    finish: str | None = None
    weathering: list[str] = Field(default_factory=list)
    reproduce_weathering_in_lego: bool = False


class OpeningVisualDescription(BaseModel):
    frame_color: str | None = None
    frame_material: str | None = None
    leaf_count: int | None = Field(default=None, ge=1, le=8)
    mullion_count: int | None = Field(default=None, ge=0, le=16)
    glazing: str | None = None
    sill: str | None = None
    surround_material: str | None = None
    surround_color: str | None = None
    notes: str | None = None


class SurveyObservation(BaseModel):
    id: str
    kind: ObservationKind
    facade: Facade | None = None
    certainty: Certainty
    statement: str = Field(min_length=1)
    evidence: list[PhotoEvidence] = Field(min_length=1)
    attributes: dict[str, Any] = Field(default_factory=dict)
    appearance: SurfaceAppearance | None = None
    opening_visual: OpeningVisualDescription | None = None


class RepresentationPolicy(BaseModel):
    """What understanding should survive, separately from LEGO fidelity."""

    preserve_nominal_materials: bool = True
    preserve_opening_composition: bool = True
    preserve_architectural_details: bool = True
    reproduce_weathering: bool = False
    reproduce_temporary_objects: bool = False


class ArchitecturalSurvey(BaseModel):
    schema_version: Literal["0.1"] = "0.1"
    id: str
    name: str
    canonical_frame: CanonicalFrame = Field(default_factory=CanonicalFrame)
    photos: list[PhotoView] = Field(min_length=1)
    known_measurements: list[KnownMeasurement] = Field(default_factory=list)
    observations: list[SurveyObservation] = Field(default_factory=list)
    representation_policy: RepresentationPolicy = Field(default_factory=RepresentationPolicy)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_survey(self) -> "ArchitecturalSurvey":
        photo_indexes = [photo.photo_index for photo in self.photos]
        if len(photo_indexes) != len(set(photo_indexes)):
            raise ValueError("photo indexes must be unique")
        if not any(photo.facade is Facade.FRONT for photo in self.photos):
            raise ValueError("survey requires at least one canonical front photo")

        measurement_kinds = [measurement.kind for measurement in self.known_measurements]
        if len(measurement_kinds) != len(set(measurement_kinds)):
            raise ValueError("survey known measurement kinds must be unique")

        observation_ids = [observation.id for observation in self.observations]
        if len(observation_ids) != len(set(observation_ids)):
            raise ValueError("survey observation IDs must be unique")

        known_photos = set(photo_indexes)
        for observation in self.observations:
            for evidence in observation.evidence:
                if evidence.photo_index not in known_photos:
                    raise ValueError(
                        f"observation {observation.id!r} references unknown photo {evidence.photo_index}"
                    )
        return self
