"""Topological Scene layer: preserve architectural relations before metric resolution."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from brickhouse.survey import Certainty, RelationKind

from .models import ArchitecturalScene as _MetricArchitecturalScene
from .models import CONNECTIVITY_TOLERANCE_M, Evidence
from .terrain_uncertainty import Terrain


class SceneRelation(BaseModel):
    """A proven architectural relation whose exact metric junction may remain unknown.

    ``semantic_anchor_volume_id`` is an append-only bridge for a Survey endpoint
    such as a ``building_boundary`` observation that deliberately does not become
    its own Scene primitive.  The Survey endpoint ID remains untouched.  When the
    rendered primitive actually touches a concrete Scene volume, this field lets
    the relation become metrically resolved without renaming the semantic anchor.
    """

    id: str
    kind: RelationKind
    subject_id: str
    object_id: str
    certainty: Certainty
    geometry_status: Literal["resolved", "unresolved"]
    semantic_anchor_volume_id: str | None = None
    statement: str = Field(min_length=1)
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_distinct_objects(self):
        if self.subject_id == self.object_id:
            raise ValueError("scene relation subject_id and object_id must differ")
        if self.geometry_status == "unresolved" and self.semantic_anchor_volume_id is not None:
            raise ValueError("unresolved scene relation cannot claim a semantic_anchor_volume_id")
        return self


class ArchitecturalScene(_MetricArchitecturalScene):
    """ArchitecturalScene v0.2 plus non-metric structural relations.

    This stays schema-version compatible and append-only. Existing Scene JSON remains
    valid because ``relations`` defaults to an empty list.
    """

    relations: list[SceneRelation] = Field(default_factory=list)
    terrain: Terrain | None = None

    @field_validator("terrain", mode="before")
    @classmethod
    def normalize_legacy_terrain(cls, value):
        if value is None or isinstance(value, dict):
            return value
        if isinstance(value, BaseModel):
            return value.model_dump(mode="python")
        return value

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
        volume_ids = {volume.id for volume in self.volumes}
        relation_ids = [relation.id for relation in self.relations]
        if len(relation_ids) != len(set(relation_ids)):
            raise ValueError("scene relation IDs must be unique")
        for relation in self.relations:
            subject_present = relation.subject_id in object_ids
            object_present = relation.object_id in object_ids
            if relation.semantic_anchor_volume_id is not None and relation.semantic_anchor_volume_id not in volume_ids:
                raise ValueError(
                    f"scene relation {relation.id!r} references unknown semantic anchor volume "
                    f"{relation.semantic_anchor_volume_id!r}"
                )
            if relation.geometry_status == "resolved":
                if subject_present and object_present:
                    if relation.semantic_anchor_volume_id is not None:
                        raise ValueError(
                            f"resolved scene relation {relation.id!r} has two Scene endpoints and must not "
                            "define semantic_anchor_volume_id"
                        )
                elif subject_present ^ object_present:
                    if relation.semantic_anchor_volume_id is None:
                        raise ValueError(
                            f"resolved scene relation {relation.id!r} has a semantic endpoint absent from the "
                            "Scene and therefore requires semantic_anchor_volume_id"
                        )
                else:
                    raise ValueError(
                        f"resolved scene relation {relation.id!r} references no Scene object"
                    )
            if relation.geometry_status == "unresolved" and not (subject_present or object_present):
                raise ValueError(
                    f"unresolved scene relation {relation.id!r} must reference at least one Scene object"
                )

    def _has_unresolved_relation(self, object_id: str) -> bool:
        return any(
            relation.geometry_status == "unresolved"
            and object_id in {relation.subject_id, relation.object_id}
            for relation in self.relations
        )

    def _validate_resolved_semantic_anchors(self) -> None:
        """Require a claimed semantic-boundary resolution to exist in metric geometry."""
        platforms = {item.id: item for item in self.platforms}
        stairs = {item.id: item for item in self.stairs}
        volumes = {item.id: item for item in self.volumes}

        for relation in self.relations:
            anchor_id = relation.semantic_anchor_volume_id
            if relation.geometry_status != "resolved" or anchor_id is None:
                continue
            if relation.kind is not RelationKind.CONNECTS_TO:
                raise ValueError(
                    f"scene relation {relation.id!r} may use semantic_anchor_volume_id only for connects_to"
                )
            present_id = (
                relation.subject_id
                if relation.subject_id in platforms or relation.subject_id in stairs
                else relation.object_id
            )
            volume = volumes[anchor_id]
            if present_id in platforms:
                holds = self._platform_touches_volume(platforms[present_id], volume)
            elif present_id in stairs:
                stair = stairs[present_id]
                holds = self._point_on_volume_boundary(stair.start, volume) or self._point_on_volume_boundary(
                    stair.end, volume
                )
            else:
                raise ValueError(
                    f"resolved semantic-anchor relation {relation.id!r} must expose a Platform or StairRun "
                    "as its Scene endpoint"
                )
            if not holds:
                raise ValueError(
                    f"resolved semantic-anchor relation {relation.id!r} is not reflected by metric contact "
                    f"with volume {anchor_id!r}"
                )

    def _validate_external_connectivity(self):
        """Allow evidenced hidden junctions but verify all claimed metric resolutions."""
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

        self._validate_resolved_semantic_anchors()
