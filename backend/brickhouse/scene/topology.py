"""Topological Scene layer: preserve architectural relations before metric resolution."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.survey import Certainty, RelationKind

from .models import ArchitecturalScene as _MetricArchitecturalScene
from .models import CONNECTIVITY_TOLERANCE_M, Evidence


class SceneRelation(BaseModel):
    """A proven architectural relation whose exact metric junction may remain unknown."""

    id: str
    kind: RelationKind
    subject_id: str
    object_id: str
    certainty: Certainty
    geometry_status: Literal["resolved", "unresolved"]
    statement: str = Field(min_length=1)
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_distinct_objects(self):
        if self.subject_id == self.object_id:
            raise ValueError("scene relation subject_id and object_id must differ")
        return self


class ArchitecturalScene(_MetricArchitecturalScene):
    """ArchitecturalScene v0.2 plus non-metric structural relations.

    This stays schema-version compatible and append-only. Existing Scene JSON remains
    valid because ``relations`` defaults to an empty list.
    """

    relations: list[SceneRelation] = Field(default_factory=list)

    def _validate_ids_and_references(self):
        super()._validate_ids_and_references()
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
        relation_ids = [relation.id for relation in self.relations]
        if len(relation_ids) != len(set(relation_ids)):
            raise ValueError("scene relation IDs must be unique")
        for relation in self.relations:
            if relation.subject_id not in object_ids or relation.object_id not in object_ids:
                raise ValueError(
                    f"scene relation {relation.id!r} references an object absent from the Scene"
                )

    def _has_unresolved_relation(self, object_id: str) -> bool:
        return any(
            relation.geometry_status == "unresolved"
            and object_id in {relation.subject_id, relation.object_id}
            for relation in self.relations
        )

    def _validate_external_connectivity(self):
        """Allow one evidenced-but-unresolved junction without inventing its coordinates.

        Existing fully metric Scenes retain the original strict behaviour. An unresolved
        topological relation may excuse a missing junction, but it never makes the Scene
        buildable: the projection boundary blocks it until the relation is resolved.
        """
        if not self.platforms and not self.stairs:
            return

        for platform in self.platforms:
            touches_metric = any(
                self._platform_touches_volume(platform, volume) for volume in self.volumes
            ) or any(
                self._point_on_platform(stair.start, platform)
                or self._point_on_platform(stair.end, platform)
                for stair in self.stairs
            )
            if not touches_metric and not self._has_unresolved_relation(platform.id):
                raise ValueError(
                    f"platform {platform.id!r} is disconnected from both building and stairs"
                )

        for stair in self.stairs:
            free_endpoints = []
            for name, point in (("start", stair.start), ("end", stair.end)):
                connected = (
                    any(self._point_on_platform(point, platform) for platform in self.platforms)
                    or any(self._point_on_volume_boundary(point, volume) for volume in self.volumes)
                    or point.z <= CONNECTIVITY_TOLERANCE_M
                )
                if not connected:
                    free_endpoints.append(name)
            if not free_endpoints:
                continue
            if len(free_endpoints) == 1 and self._has_unresolved_relation(stair.id):
                continue
            raise ValueError(
                f"stair {stair.id!r} {', '.join(free_endpoints)} does not connect to ground, a platform, or the building"
            )
