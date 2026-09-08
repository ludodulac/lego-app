"""Versioned modular architectural priors for measurement-free scale inference.

Module catalogues are statistical references only. A counted module grid may help
bound an opening dimension, but neither the catalogue nor the count becomes a
Survey measurement.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .scale_estimation import ArchitecturalDimensionPrior, ArchitecturalPriorProvenance


GLASS_BLOCK_PRIOR_CATALOG_VERSION = "glass-block-priors-0.1"

_REFERENCE = (
    "Seves Glassblock Technical Guide 2025/03 and Basic Line accessories; "
    "recurrent 19x19x8 cm glass block format, with documented 10 mm and 16 mm spacers"
)


class GlassBlockGridPriorQuery(BaseModel):
    axis: Literal["width", "height"]
    module_count: int = Field(ge=1, le=100)


def glass_block_grid_prior_v01(
    query: GlassBlockGridPriorQuery,
) -> ArchitecturalDimensionPrior:
    """Return a conservative dimension prior for a visually counted module run.

    The lower bound is the sum of nominal 19 cm blocks. The upper bound allows
    documented joint sizes up to 16 mm plus small edge tolerance; it deliberately
    does not claim an exact frame/opening size. Older installations can differ.
    """
    count = query.module_count
    nominal_block_m = 0.19
    typical_joint_m = 0.01
    max_joint_m = 0.016
    edge_tolerance_m = 0.02

    min_m = count * nominal_block_m
    typical_m = min_m + max(0, count - 1) * typical_joint_m
    max_m = min_m + max(0, count - 1) * max_joint_m + edge_tolerance_m

    return ArchitecturalDimensionPrior(
        id=(
            f"{GLASS_BLOCK_PRIOR_CATALOG_VERSION}:19cm-grid:"
            f"{query.axis}:{count}-modules"
        ),
        feature_kind=f"glass_block_grid_{count}_modules",
        dimension=query.axis,
        min_m=min_m,
        max_m=max_m,
        typical_m=typical_m,
        confidence=0.54,
        provenance=ArchitecturalPriorProvenance(
            reference=_REFERENCE,
            context=(
                f"{GLASS_BLOCK_PRIOR_CATALOG_VERSION}; {count} visually counted modules along {query.axis}. "
                "Prior bounds module-run extent only; frame edges, old formats and renovation conditions may differ."
            ),
        ),
    )
