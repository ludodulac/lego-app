"""Append-only wall-profile extension of the canonical ArchitecturalScene."""
from __future__ import annotations

from pydantic import Field

from brickhouse.survey import RelationKind

from .models import CONNECTIVITY_TOLERANCE_M, EPSILON
from .topology import ArchitecturalScene as _TopologyArchitecturalScene
from .wall_profile import WallProfileObservation


class ArchitecturalScene(_TopologyArchitecturalScene):
    """ArchitecturalScene with evidence-backed facade depth observations.

    Existing v0.2 JSON remains valid because this collection defaults to empty.
    The inherited Scene validator calls overridden audit methods dynamically, so
    append-only wall-profile and structural-support contracts can participate in
    canonical validation without weakening older topology contracts.
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

    @staticmethod
    def _volume_supports_platform(volume, platform) -> bool | None:
        """Audit a resolved architectural load path without inventing missing metrics.

        A volume supports a platform when the platform is horizontally over the
        volume by a positive area and its walking-surface level coincides with the
        volume top within the canonical Scene connectivity tolerance.  ``None``
        deliberately means the volume envelope is incomplete, so evidence remains
        uncertainty instead of becoming a fabricated geometric contradiction.
        """
        if any(value is None for value in (volume.width.value, volume.depth.value, volume.height.value)):
            return None

        volume_top = volume.position.z + volume.height.value
        if abs(platform.position.z - volume_top) > CONNECTIVITY_TOLERANCE_M:
            return False

        vx0, vx1 = volume.position.x, volume.position.x + volume.width.value
        vy0, vy1 = volume.position.y, volume.position.y + volume.depth.value
        px0, px1 = platform.position.x, platform.position.x + platform.width
        py0, py1 = platform.position.y, platform.position.y + platform.depth
        overlap_x = min(vx1, px1) - max(vx0, px0)
        overlap_y = min(vy1, py1) - max(vy0, py0)
        return overlap_x > EPSILON and overlap_y > EPSILON

    def _validate_resolved_scene_relations(self) -> None:
        """Extend resolved topology auditing to directional ``supports`` claims."""
        super()._validate_resolved_scene_relations()
        volumes = {item.id: item for item in self.volumes}
        platforms = {item.id: item for item in self.platforms}

        for relation in self.relations:
            if relation.geometry_status != "resolved" or relation.kind is not RelationKind.SUPPORTS:
                continue
            # This first structural slice intentionally audits the concrete pair
            # required by raised landings/decks. Other support pair types stay
            # unclaimed rather than being guessed from generic proximity.
            volume = volumes.get(relation.subject_id)
            platform = platforms.get(relation.object_id)
            if volume is None or platform is None:
                continue
            holds = self._volume_supports_platform(volume, platform)
            if holds is False:
                raise ValueError(
                    f"resolved scene relation {relation.id!r} supports is not reflected by metric bearing "
                    f"from volume {relation.subject_id!r} to platform {relation.object_id!r}"
                )
