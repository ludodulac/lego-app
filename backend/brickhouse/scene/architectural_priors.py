"""Versioned statistical architectural priors for measurement-free scale inference.

These values describe recurrent catalogue dimensions, not facts about a photographed
building. They must stay in the inference layer and must never be serialized as
Survey observations, user measurements, or observed evidence.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from .scale_estimation import ArchitecturalDimensionPrior, ArchitecturalPriorProvenance


FR_OPENING_PRIOR_CATALOG_VERSION = "fr-opening-priors-0.1"

_REFERENCE = (
    "WIBAIE, Dimensions standard des baies et fenêtres, 2026-07-30; "
    "Préfal, Quelle est la dimension d'une fenêtre standard?, consulted 2026-09"
)


class OpeningPriorQuery(BaseModel):
    """Context used to select a conservative opening prior family."""

    semantic_type: Literal["window", "door_or_glazed_door"]
    leaf_count: int | None = Field(default=None, ge=1, le=8)
    country_context: Literal["FR"] = "FR"


def _provenance(context: str) -> ArchitecturalPriorProvenance:
    return ArchitecturalPriorProvenance(
        reference=_REFERENCE,
        context=(
            f"{FR_OPENING_PRIOR_CATALOG_VERSION}; {context}. "
            "Recurring French catalogue dimensions only; renovation and older buildings may be atypical."
        ),
    )


def _prior(
    *,
    suffix: str,
    feature_kind: str,
    dimension: Literal["width", "height"],
    min_m: float,
    max_m: float,
    typical_m: float,
    confidence: float,
    context: str,
) -> ArchitecturalDimensionPrior:
    return ArchitecturalDimensionPrior(
        id=f"{FR_OPENING_PRIOR_CATALOG_VERSION}:{suffix}:{dimension}",
        feature_kind=feature_kind,
        dimension=dimension,
        min_m=min_m,
        max_m=max_m,
        typical_m=typical_m,
        confidence=confidence,
        provenance=_provenance(context),
    )


def france_residential_opening_priors_v01(
    query: OpeningPriorQuery,
) -> list[ArchitecturalDimensionPrior]:
    """Return conservative FR opening priors for one semantic/configuration context.

    When leaf count is unknown, ranges are deliberately broadened and confidence
    reduced. That is preferable to silently selecting a two-leaf modern standard
    for an old or renovated opening.
    """
    if query.semantic_type == "window" and query.leaf_count == 1:
        return [
            _prior(
                suffix="window-1leaf",
                feature_kind="window_1_leaf",
                dimension="width",
                min_m=0.40,
                max_m=0.80,
                typical_m=0.60,
                confidence=0.50,
                context="one-leaf window; recurrent WIBAIE/Préfal catalogue widths",
            ),
            _prior(
                suffix="window-1leaf",
                feature_kind="window_1_leaf",
                dimension="height",
                min_m=0.60,
                max_m=1.25,
                typical_m=0.75,
                confidence=0.42,
                context="one-leaf window; broad recurrent catalogue height range",
            ),
        ]

    if query.semantic_type == "window" and query.leaf_count == 2:
        return [
            _prior(
                suffix="window-2leaf",
                feature_kind="window_2_leaf",
                dimension="width",
                min_m=1.00,
                max_m=1.20,
                typical_m=1.10,
                confidence=0.62,
                context="two-leaf window; WIBAIE and Préfal recurrent French widths",
            ),
            _prior(
                suffix="window-2leaf",
                feature_kind="window_2_leaf",
                dimension="height",
                min_m=1.05,
                max_m=1.35,
                typical_m=1.20,
                confidence=0.58,
                context="two-leaf window; recurrent WIBAIE/Préfal heights",
            ),
        ]

    if query.semantic_type == "window":
        return [
            _prior(
                suffix="window-leaves-unknown",
                feature_kind="window_leaf_count_unknown",
                dimension="width",
                min_m=0.40,
                max_m=1.20,
                typical_m=0.90,
                confidence=0.26,
                context="window leaf count unknown; union of common one- and two-leaf catalogue widths",
            ),
            _prior(
                suffix="window-leaves-unknown",
                feature_kind="window_leaf_count_unknown",
                dimension="height",
                min_m=0.60,
                max_m=1.35,
                typical_m=1.05,
                confidence=0.24,
                context="window leaf count unknown; intentionally broad recurrent height range",
            ),
        ]

    if query.semantic_type == "door_or_glazed_door" and query.leaf_count == 1:
        return [
            _prior(
                suffix="glazed-door-1leaf",
                feature_kind="glazed_door_1_leaf",
                dimension="width",
                min_m=0.80,
                max_m=0.90,
                typical_m=0.85,
                confidence=0.58,
                context="one-leaf porte-fenêtre; recurrent WIBAIE widths",
            ),
            _prior(
                suffix="glazed-door-1leaf",
                feature_kind="glazed_door_1_leaf",
                dimension="height",
                min_m=2.05,
                max_m=2.25,
                typical_m=2.15,
                confidence=0.42,
                context=(
                    "one-leaf porte-fenêtre; interval deliberately widened around the recurrent "
                    "2.15 m WIBAIE catalogue height to avoid treating it as an exact standard"
                ),
            ),
        ]

    return [
        _prior(
            suffix="glazed-door-leaves-unknown",
            feature_kind="glazed_door_configuration_unknown",
            dimension="width",
            min_m=0.80,
            max_m=2.40,
            typical_m=1.20,
            confidence=0.20,
            context=(
                "glazed door configuration unknown; broad range spans recurrent one-leaf porte-fenêtre "
                "and common glazed-bay widths"
            ),
        ),
        _prior(
            suffix="glazed-door-leaves-unknown",
            feature_kind="glazed_door_configuration_unknown",
            dimension="height",
            min_m=1.95,
            max_m=2.25,
            typical_m=2.15,
            confidence=0.24,
            context="glazed door configuration unknown; intentionally broad height plausibility range",
        ),
    ]
