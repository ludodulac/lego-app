"""Deterministic support-chain audit for canonical orthogonal LEGO wall bricks.

A canonical part ID does not by itself define connection semantics. Scene-native
terraces, stairs, chimneys, terrain and glazing may deliberately reuse BRICK_* as a
rendering primitive while belonging to another connection domain. This first
physical-validity slice therefore owns only final BrickModel parts explicitly marked
as ``component='wall'`` and ``category='brick'``. Roofs and facade-detail systems keep
their dedicated validators until their support/connection semantics are explicit.
"""
from __future__ import annotations

from collections import defaultdict

from pydantic import BaseModel, Field

from .brick_model import BrickModel, BrickModelPart
from .catalog import create_m0_brick_catalog


class StandardBrickSupportNode(BaseModel):
    placement_id: str
    z_bottom_plates: int = Field(ge=0)
    z_top_plates: int = Field(gt=0)
    footprint: set[tuple[int, int]]
    supporters: list[str] = Field(default_factory=list)
    reaches_ground: bool = False


class StandardBrickSupportReport(BaseModel):
    audited_placement_ids: list[str] = Field(default_factory=list)
    unsupported_placement_ids: list[str] = Field(default_factory=list)
    nodes: list[StandardBrickSupportNode] = Field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.unsupported_placement_ids


def _standard_brick_definitions():
    return {item.id: item for item in create_m0_brick_catalog().bricks}


def _is_orthogonal_wall_brick(part: BrickModelPart, definitions) -> bool:
    """Return whether BH-166 owns this placement's connection semantics."""
    return (
        part.component == "wall"
        and part.category == "brick"
        and part.part_id in definitions
    )


def _footprint(part: BrickModelPart, definition) -> set[tuple[int, int]]:
    width, length = definition.footprint(part.rotation_quarter_turns)
    return {
        (part.x_studs + dx, part.y_studs + dy)
        for dx in range(width)
        for dy in range(length)
    }


def _wall_structural_datum(model: BrickModel, audited: list[BrickModelPart]) -> int:
    """Return the z datum from which this wall shell must be continuously supported.

    Ordinarily the LEGO wall datum is global z=0. Scene-aware framing can translate
    the complete architectural building upward when observed terrain extends below
    the building's architectural zero. That translation is a coordinate-frame change,
    not evidence that the complete wall shell became physically floating. In that
    specific case, preserve the lowest wall course as the wall's structural datum.

    This does *not* validate the terrain assembly or claim that terrain supports the
    building. It only keeps the local wall-chain invariant scoped to its architectural
    host datum; scene-level host/foundation connectivity remains a separate gate.
    """
    if not audited:
        return 0
    wall_base = min(part.z_plates for part in audited)
    if wall_base == 0:
        return 0
    has_lower_scene_terrain = any(
        part.category == "terrain" and part.z_plates < wall_base
        for part in model.parts
    )
    return wall_base if has_lower_scene_terrain else 0


def analyze_standard_brick_support_chain(model: BrickModel) -> StandardBrickSupportReport:
    """Return a transitive wall-support report without mutating ``model``.

    Every canonical orthogonal wall brick at the wall structural datum is anchored.
    Every higher audited wall brick must share at least one stud cell with another
    audited wall brick whose top is exactly at its bottom. Since all edges descend in
    z, reachability can be evaluated in one stable bottom-up pass.
    """
    definitions = _standard_brick_definitions()
    audited = [
        part for part in model.parts
        if _is_orthogonal_wall_brick(part, definitions)
    ]
    audited.sort(key=lambda part: (part.z_plates, part.placement_id))
    structural_datum = _wall_structural_datum(model, audited)

    by_top: dict[int, list[StandardBrickSupportNode]] = defaultdict(list)
    nodes: list[StandardBrickSupportNode] = []
    unsupported: list[str] = []

    for part in audited:
        definition = definitions[part.part_id]
        footprint = _footprint(part, definition)
        possible_supporters = by_top.get(part.z_plates, [])
        supporters = sorted(
            node.placement_id
            for node in possible_supporters
            if node.footprint.intersection(footprint)
        )
        reaches_ground = part.z_plates == structural_datum or any(
            node.reaches_ground
            for node in possible_supporters
            if node.placement_id in supporters
        )
        node = StandardBrickSupportNode(
            placement_id=part.placement_id,
            z_bottom_plates=part.z_plates,
            z_top_plates=part.z_plates + definition.height_plates,
            footprint=footprint,
            supporters=supporters,
            reaches_ground=reaches_ground,
        )
        nodes.append(node)
        by_top[node.z_top_plates].append(node)
        if not reaches_ground:
            unsupported.append(part.placement_id)

    return StandardBrickSupportReport(
        audited_placement_ids=[part.placement_id for part in audited],
        unsupported_placement_ids=sorted(unsupported),
        nodes=nodes,
    )


def validate_standard_brick_support_chain(model: BrickModel) -> None:
    """Reject orthogonal wall bricks without a continuous chain to their host datum."""
    report = analyze_standard_brick_support_chain(model)
    if report.unsupported_placement_ids:
        raise ValueError(
            "BrickModel contains orthogonal wall bricks without a continuous stud/tube support chain to their structural datum: "
            + ", ".join(report.unsupported_placement_ids)
        )
