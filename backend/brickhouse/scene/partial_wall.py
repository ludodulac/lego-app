"""Partial architectural wall geometry without implicit enclosure semantics."""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import Position3D, SourceInfo

from .models import EPSILON, Evidence, ExteriorMaterial, PropertyValue


class PartialWallSegment(BaseModel):
    """One evidence-backed vertical wall segment, not a closed architectural volume.

    ``start`` and ``end`` define the horizontal baseline in Scene coordinates and
    ``height`` extends vertically from that baseline.  The model deliberately has
    no enclosure, room, host-volume or hidden-face semantics.  ``thickness`` is
    optional and may carry ``value=None`` when evidence proves wall existence but
    does not calibrate its architectural thickness.
    """

    id: str
    start: Position3D
    end: Position3D
    height: PropertyValue
    thickness: PropertyValue | None = None
    material: ExteriorMaterial | None = None
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_vertical_segment(self):
        if abs(self.start.z - self.end.z) > EPSILON:
            raise ValueError("partial wall segment baseline must be horizontal")
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        if dx * dx + dy * dy <= EPSILON * EPSILON:
            raise ValueError("partial wall segment baseline must have positive plan length")
        return self
