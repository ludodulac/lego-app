"""Curated LEGO architectural opening motifs.

This module is intentionally downstream of BuildingModel/ArchitecturalScene.  It
turns the small set of engine-validated LEGO window assemblies into reusable
architectural motifs with explicit footprint and connection metadata.  Raw part
catalog entries are not architectural solutions by themselves.

BH-162 starts conservatively: only parts already validated by BrickHouse are
registered here.  New LEGO elements must first be added to the engine capability
registry/tests before they may become motifs.
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
]
OpeningMotifComposition = Literal["single", "paired", "four_pane"]


class OpeningMotif(BaseModel):
    """One approved architectural use of catalog-backed LEGO parts."""

    id: str
    role: OpeningMotifRole
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
    connection_strategy: Literal["stud_bearing_in_wall_opening"] = "stud_bearing_in_wall_opening"


def _motif(
    *,
    assembly_id: str,
    role: OpeningMotifRole,
    composition: OpeningMotifComposition,
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
        composition=composition,
        assembly_id=assembly.id,
        frame_part_id=assembly.frame_part_id,
        pane_part_id=assembly.pane_part_id,
        module_count=modules,
        width_studs=width,
        height_bricks=height,
        leaf_count=leaves,
        pane_count=panes,
    )


# This registry is deliberately curated rather than generated as a Cartesian
# product.  A technically tileable combination does not automatically become an
# architecturally acceptable motif.
OPENING_MOTIFS: tuple[OpeningMotif, ...] = (
    _motif(assembly_id="window-1x2x2-60592-60601", role="window", composition="single"),
    _motif(assembly_id="window-1x2x3-60593-60602", role="tall_window", composition="single"),
    _motif(assembly_id="window-1x4x3-60594-60603", role="window", composition="single"),
    _motif(assembly_id="window-1x2x2-60592-60601", role="paired_window", composition="paired"),
    _motif(assembly_id="window-1x2x3-60593-60602", role="paired_window", composition="paired"),
    _motif(assembly_id="window-1x2x2-60592-60601", role="four_pane_window", composition="four_pane"),
    _motif(assembly_id="window-1x2x3-60593-60602", role="four_pane_window", composition="four_pane"),
)


def opening_motifs_for_topology(
    *,
    leaf_count: int | None,
    pane_count: int | None,
) -> tuple[OpeningMotif, ...]:
    """Return deterministic motifs that do not contradict known topology.

    When no topology is known, only single-module motifs are eligible.  This
    preserves the long-standing rule that LEGO convenience cannot invent
    mullions/leaves.  Known counts are hard filters rather than scoring hints.
    """
    if leaf_count is not None and leaf_count <= 0:
        raise ValueError("leaf_count must be positive when provided")
    if pane_count is not None and pane_count <= 0:
        raise ValueError("pane_count must be positive when provided")

    if leaf_count is None and pane_count is None:
        return tuple(motif for motif in OPENING_MOTIFS if motif.composition == "single")
    return tuple(
        motif
        for motif in OPENING_MOTIFS
        if (leaf_count is None or motif.leaf_count == leaf_count)
        and (pane_count is None or motif.pane_count == pane_count)
    )


def opening_motif_by_id(motif_id: str) -> OpeningMotif | None:
    return next((motif for motif in OPENING_MOTIFS if motif.id == motif_id), None)
