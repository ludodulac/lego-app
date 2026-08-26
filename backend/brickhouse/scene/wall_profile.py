"""Evidence-backed facade depth observations kept separate from guessed construction metrics."""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import Facade, SourceInfo

from .models import EPSILON, Evidence, PropertyValue


class WallProfileObservation(BaseModel):
    """What the photos establish about a facade's wall/reveal depth.

    A photo can prove that openings are recessed without proving a numeric wall
    thickness. ``PropertyValue`` deliberately permits ``value=None`` so the Scene
    can retain that architectural fact without inventing centimeters.
    """

    id: str
    volume_id: str
    facade: Facade
    openings_recessed: bool | None = None
    wall_thickness: PropertyValue | None = None
    reveal_depth: PropertyValue | None = None
    source: SourceInfo
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_claims(self):
        if self.openings_recessed is None and self.wall_thickness is None and self.reveal_depth is None:
            raise ValueError("wall profile observation must contain at least one architectural claim")
        thickness = self.wall_thickness.value if self.wall_thickness is not None else None
        reveal = self.reveal_depth.value if self.reveal_depth is not None else None
        if thickness is not None and reveal is not None and reveal > thickness + EPSILON:
            raise ValueError("wall reveal_depth cannot exceed wall_thickness")
        if self.openings_recessed is False and reveal is not None and reveal > EPSILON:
            raise ValueError("positive reveal_depth conflicts with openings_recessed=false")
        return self
