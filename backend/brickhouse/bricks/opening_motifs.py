"""Curated LEGO architectural opening motifs.

This module is intentionally downstream of BuildingModel/ArchitecturalScene. It
turns the small set of engine-validated LEGO frame/pane assemblies into reusable
architectural motifs with explicit footprint and connection metadata. Raw part
catalog entries are not architectural solutions by themselves.

Only parts already validated by BrickHouse are registered here. A motif may use a
validated framed-glazing assembly for more than one architectural semantic role,
but the source opening type is never changed to make that possible.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .windows import VALIDATED_WINDOW_ASSEMBLIES

OpeningMotifRole = Literal[
    "window",
    "tall_window",
    "paired_window",
    "four_pane_window",
    "glazed_door",
    "neutral_glazed",
]
OpeningRepresentationRole = Literal["window", "glazed_door", "neutral_glazed"]
OpeningMotifComposition = Literal["single", "paired", "four_pane"]
OpeningMotifOrientation = Literal["vertical_in_facade"]
OpeningMotifSupportRequirement = Literal[
    "surrounding_wall_bearing",
    "threshold_or_surrounding_wall_bearing",
]


class OpeningMotif(BaseModel):
    """One approved architectural use of placement-validated LEGO parts."""

    id: str
    role: OpeningMotifRole
    representation_role: OpeningRepresentationRole
    composition: OpeningMotifComposition
    assembly_id: str
    frame_part_id: str
    pane_part_id: str
    module_count: int = Field(gt=0)
    width_studs: int = Field(gt=0)
    height_bricks: int = Field(gt=0)
    depth_studs: int = Field(default=1, gt=0)
    leaf_count: int = Field(gt=0)
    pane_count: int = Field(gt=0)
    orientation: OpeningMotifOrientation = "vertical_in_facade"
    connection_strategy: Literal["stud_bearing_in_wall_opening"] = "stud_bearing_in_wall_opening"
    support_requirement: OpeningMotifSupportRequirement = "surrounding_wall_bearing"


def _motif(
    *,
    assembly_id: str,
    role: OpeningMotifRole,
    representation_role: OpeningRepresentationRole,
    composition: OpeningMotifComposition,
    support_requirement: OpeningMotifSupportRequirement = "surrounding_wall_bearing",
) -> OpeningMotif:
    assembly = next(item for item in VALIDATED_WINDOW_ASSEMBLIES if item.id == assembly_id)
    if composition == "single":
        modules, width, height, leaves, panes = 1, assembly.width_studs, assembly.height_bricks, 1, 1
    elif composition == "paired":
        modules, width, height, leaves, panes = 2, assembly.width_studs * 2, assembly.height_bricks, 2, 2
    else:
        modules, width, height, leaves, panes = 4, assembly.width_studs * 2, assembly.height_bricks * 2, 2, 4
    return OpeningMotif(
        id=f"{role}:{assembly.id}:{composition}",
        role=role,
        representation_role=representation_role,
        composition=composition,
        assembly_id=assembly.id,
        frame_part_id=assembly.frame_part_id,
        pane_part_id=assembly.pane_part_id,
        module_count=modules,
        width_studs=width,
        height_bricks=height,
        leaf_count=leaves,
        pane_count=panes,
        support_requirement=support_requirement,
    )


# Curated rather than generated as a Cartesian product. A technically tileable
# combination does not automatically become an architectural motif.
OPENING_MOTIFS: tuple[OpeningMotif, ...] = (
    _motif(assembly_id="window-1x2x2-60592-60601", role="window", representation_role="window", composition="single"),
    _motif(assembly_id="window-1x2x3-60593-60602", role="tall_window", representation_role="window", composition="single"),
    _motif(assembly_id="window-1x4x3-60594-60603", role="window", representation_role="window", composition="single"),
    _motif(assembly_id="window-1x2x2-60592-60601", role="paired_window", representation_role="window", composition="paired"),
    _motif(assembly_id="window-1x2x3-60593-60602", role="paired_window", representation_role="window", composition="paired"),
    _motif(assembly_id="window-1x2x2-60592-60601", role="four_pane_window", representation_role="window", composition="four_pane"),
    _motif(assembly_id="window-1x2x3-60593-60602", role="four_pane_window", representation_role="window", composition="four_pane"),
    # Door-compatible uses deliberately reuse only already placement-approved
    # framed-glazing assemblies. They preserve DOOR semantics and require a
    # threshold/surrounding-wall bearing anchor; no door-specific part is invented.
    _motif(assembly_id="window-1x2x3-60593-60602", role="glazed_door", representation_role="glazed_door", composition="single", support_requirement="threshold_or_surrounding_wall_bearing"),
    _motif(assembly_id="window-1x2x3-60593-60602", role="glazed_door", representation_role="glazed_door", composition="paired", support_requirement="threshold_or_surrounding_wall_bearing"),
    _motif(assembly_id="window-1x2x3-60593-60602", role="glazed_door", representation_role="glazed_door", composition="four_pane", support_requirement="threshold_or_surrounding_wall_bearing"),
    # UNKNOWN means semantic subtype is unresolved, not that visible glazing is
    # absent. Neutral motifs expose framed glazing while retaining UNKNOWN.
    _motif(assembly_id="window-1x2x3-60593-60602", role="neutral_glazed", representation_role="neutral_glazed", composition="single"),
    _motif(assembly_id="window-1x4x3-60594-60603", role="neutral_glazed", representation_role="neutral_glazed", composition="single"),
)


def opening_motifs_for_representation(
    *,
    representation_role: OpeningRepresentationRole,
    leaf_count: int | None,
    pane_count: int | None,
) -> tuple[OpeningMotif, ...]:
    """Return motifs that preserve both semantic role and known composition."""
    if leaf_count is not None and leaf_count <= 0:
        raise ValueError("leaf_count must be positive when provided")
    if pane_count is not None and pane_count <= 0:
        raise ValueError("pane_count must be positive when provided")

    eligible = tuple(
        motif for motif in OPENING_MOTIFS
        if motif.representation_role == representation_role
    )
    if leaf_count is None and pane_count is None:
        return tuple(motif for motif in eligible if motif.composition == "single")
    return tuple(
        motif
        for motif in eligible
        if (leaf_count is None or motif.leaf_count == leaf_count)
        and (pane_count is None or motif.pane_count == pane_count)
    )


def opening_motifs_for_topology(
    *,
    leaf_count: int | None,
    pane_count: int | None,
) -> tuple[OpeningMotif, ...]:
    """Compatibility API for architectural windows only."""
    return opening_motifs_for_representation(
        representation_role="window",
        leaf_count=leaf_count,
        pane_count=pane_count,
    )


def opening_motif_by_id(motif_id: str) -> OpeningMotif | None:
    return next((motif for motif in OPENING_MOTIFS if motif.id == motif_id), None)
