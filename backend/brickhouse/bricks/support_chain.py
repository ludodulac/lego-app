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
    """Return whether BH-166 owns this placement's connection semantics.

    Connection-domain ownership is explicit rather than inferred from ``part_id``.
    A BRICK_1X1 used as timber decking, terrain, glazing or another facade detail is
    intentionally excluded here; those systems must prove their own host/support
    chains instead of being accidentally validated by wall rules.
    """
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


def analyze_standard_brick_support_chain(model: BrickModel) -> StandardBrickSupportReport:
    """Return a transitive ground-support report without mutating ``model``.

    A canonical orthogonal wall brick at ground level is anchored. Every other
    audited wall brick must share at least one stud cell with another audited wall
    brick whose top is exactly at its bottom. Since all edges descend in z,
    reachability can be evaluated in one stable bottom-up pass.
    """
    definitions = _standard_brick_definitions()
    audited = [
        part for part in model.parts
        if _is_orthogonal_wall_brick(part, definitions)
    ]
    audited.sort(key=lambda part: (part.z_plates, part.placement_id))

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
        reaches_ground = part.z_plates == 0 or any(
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
    """Reject orthogonal wall bricks whose stud/tube chain cannot reach ground."""
    report = analyze_standard_brick_support_chain(model)
    if report.unsupported_placement_ids:
        raise ValueError(
            "BrickModel contains orthogonal wall bricks without a continuous stud/tube support chain to ground: "
            + ", ".join(report.unsupported_placement_ids)
        )
