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
    its own Scene primitive. The Survey endpoint ID remains untouched. When the
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

    def _has_resolved_semantic_anchor_claim(self, object_id: str) -> bool:
        """Defer claimed semantic-anchor connectivity to its stricter metric audit."""
        return any(
            relation.geometry_status == "resolved"
            and relation.semantic_anchor_volume_id is not None
            and object_id in {relation.subject_id, relation.object_id}
            for relation in self.relations
        )

    @staticmethod
    def _platforms_touch(first, second) -> bool:
        """Treat coplanar touching/overlapping walkable surfaces as connected."""
        if abs(first.position.z - second.position.z) > CONNECTIVITY_TOLERANCE_M:
            return False
        ax0, ax1 = first.position.x, first.position.x + first.width
        ay0, ay1 = first.position.y, first.position.y + first.depth
        bx0, bx1 = second.position.x, second.position.x + second.width
        by0, by1 = second.position.y, second.position.y + second.depth
        x_gap = max(0.0, max(ax0, bx0) - min(ax1, bx1))
        y_gap = max(0.0, max(ay0, by0) - min(ay1, by1))
        return x_gap <= CONNECTIVITY_TOLERANCE_M and y_gap <= CONNECTIVITY_TOLERANCE_M

    @staticmethod
    def _volumes_touch(first, second) -> bool:
        """Accept a secondary Scene volume as the metric endpoint of a semantic building boundary."""
        if any(
            value is None
            for value in (
                first.width.value,
                first.depth.value,
                first.height.value,
                second.width.value,
                second.depth.value,
                second.height.value,
            )
        ):
            return False
        ax0, ax1 = first.position.x, first.position.x + first.width.value
        ay0, ay1 = first.position.y, first.position.y + first.depth.value
        az0, az1 = first.position.z, first.position.z + first.height.value
        bx0, bx1 = second.position.x, second.position.x + second.width.value
        by0, by1 = second.position.y, second.position.y + second.depth.value
        bz0, bz1 = second.position.z, second.position.z + second.height.value

        x_overlap = min(ax1, bx1) >= max(ax0, bx0) - CONNECTIVITY_TOLERANCE_M
        y_overlap = min(ay1, by1) >= max(ay0, by0) - CONNECTIVITY_TOLERANCE_M
        z_overlap = min(az1, bz1) >= max(az0, bz0) - CONNECTIVITY_TOLERANCE_M
        x_boundary = min(abs(ax0 - bx1), abs(ax1 - bx0)) <= CONNECTIVITY_TOLERANCE_M
        y_boundary = min(abs(ay0 - by1), abs(ay1 - by0)) <= CONNECTIVITY_TOLERANCE_M
        z_boundary = min(abs(az0 - bz1), abs(az1 - bz0)) <= CONNECTIVITY_TOLERANCE_M
        return (
            (x_boundary and y_overlap and z_overlap)
            or (y_boundary and x_overlap and z_overlap)
            or (z_boundary and x_overlap and y_overlap)
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
            scene_endpoint_ids = {relation.subject_id, relation.object_id}
            present_id = next(
                (item_id for item_id in scene_endpoint_ids if item_id in platforms or item_id in stairs or item_id in volumes),
                None,
            )
            volume = volumes[anchor_id]
            if present_id in platforms:
                holds = self._platform_touches_volume(platforms[present_id], volume)
            elif present_id in stairs:
                stair = stairs[present_id]
                holds = self._point_on_volume_boundary(stair.start, volume) or self._point_on_volume_boundary(
                    stair.end, volume
                )
            elif present_id in volumes:
                holds = present_id != anchor_id and self._volumes_touch(volumes[present_id], volume)
            else:
                raise ValueError(
                    f"resolved semantic-anchor relation {relation.id!r} must expose a Platform, StairRun, "
                    "or secondary Scene volume as its Scene endpoint"
                )
            if not holds:
                raise ValueError(
                    f"resolved semantic-anchor relation {relation.id!r} is not reflected by metric contact "
                    f"with volume {anchor_id!r}"
                )

    def _validate_external_connectivity(self):
        """Allow evidenced hidden junctions but verify all claimed metric resolutions."""
        self._validate_resolved_semantic_anchors()
        if not self.platforms and not self.stairs:
            return

        for platform in self.platforms:
            touches_metric = any(
                self._platform_touches_volume(platform, volume) for volume in self.volumes
            ) or any(
                other.id != platform.id and self._platforms_touch(platform, other)
                for other in self.platforms
            ) or any(
                self._point_on_platform(stair.start, platform)
                or self._point_on_platform(stair.end, platform)
                for stair in self.stairs
            )
            if (
                not touches_metric
                and not self._has_unresolved_relation(platform.id)
                and not self._has_resolved_semantic_anchor_claim(platform.id)
            ):
                # Preserve the historical substring used by clients/tests while
                # making the new platform-to-platform possibility explicit.
                raise ValueError(
                    f"platform {platform.id!r} is disconnected from both building and stairs and from other platforms"
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
            if len(free_endpoints) == 1 and self._has_resolved_semantic_anchor_claim(stair.id):
                continue
            raise ValueError(
                f"stair {stair.id!r} {', '.join(free_endpoints)} does not connect to ground, a platform, or the building"
            )
