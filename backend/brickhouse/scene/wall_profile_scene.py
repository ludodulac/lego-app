"""Append-only wall-profile extension of the canonical ArchitecturalScene."""
from __future__ import annotations

from pydantic import Field

from .topology import ArchitecturalScene as _TopologyArchitecturalScene
from .wall_profile import WallProfileObservation


class ArchitecturalScene(_TopologyArchitecturalScene):
    """ArchitecturalScene with evidence-backed facade depth observations.

    Existing v0.2 JSON remains valid because this collection defaults to empty.
    The inherited Scene validator calls this overridden reference audit, so wall
    profile observations participate in canonical validation without changing
    older topology contracts.
    """

    wall_profile_observations: list[WallProfileObservation] = Field(default_factory=list)

    def _validate_ids_and_references(self):
        super()._validate_ids_and_references()
        volume_ids = {volume.id for volume in self.volumes}
        object_ids = {
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
        }
        profile_ids = [profile.id for profile in self.wall_profile_observations]
        if len(profile_ids) != len(set(profile_ids)):
            raise ValueError("wall profile observation IDs must be unique")
        if object_ids.intersection(profile_ids):
            raise ValueError("wall profile observation IDs must not collide with Scene object IDs")

        scopes = []
        for profile in self.wall_profile_observations:
            if profile.volume_id not in volume_ids:
                raise ValueError(
                    f"wall profile observation {profile.id!r} references unknown volume {profile.volume_id!r}"
                )
            scopes.append((profile.volume_id, profile.facade))
        if len(scopes) != len(set(scopes)):
            raise ValueError("at most one wall profile observation may be defined per volume/facade")
