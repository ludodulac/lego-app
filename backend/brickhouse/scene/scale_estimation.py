"""Robust architectural scale estimation from visual ratios and statistical priors.

This module deliberately sits outside ArchitecturalSurvey source truth. Priors are
statistical references, not observations of the photographed building, and a
ScaleEstimate is always inferred. Nothing here creates or mutates
``known_measurements``.
"""
from __future__ import annotations

from statistics import median
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from brickhouse.building import SourceInfo, SourceKind


class ArchitecturalPriorProvenance(BaseModel):
    kind: Literal["statistical_prior"] = "statistical_prior"
    reference: str = Field(min_length=1)
    context: str | None = None


class ArchitecturalDimensionPrior(BaseModel):
    """Plausible real-world dimension range for one architectural feature."""

    id: str = Field(min_length=1)
    feature_kind: str = Field(min_length=1)
    dimension: Literal["width", "height", "length"]
    min_m: float = Field(gt=0)
    max_m: float = Field(gt=0)
    typical_m: float | None = Field(default=None, gt=0)
    confidence: float = Field(default=0.6, gt=0, le=1)
    provenance: ArchitecturalPriorProvenance

    @model_validator(mode="after")
    def validate_range(self) -> "ArchitecturalDimensionPrior":
        if self.max_m <= self.min_m:
            raise ValueError("architectural prior max_m must be greater than min_m")
        if self.typical_m is not None and not self.min_m <= self.typical_m <= self.max_m:
            raise ValueError("architectural prior typical_m must lie inside [min_m, max_m]")
        return self

    @property
    def center_m(self) -> float:
        return self.typical_m if self.typical_m is not None else (self.min_m + self.max_m) / 2


class VisualScaleCue(BaseModel):
    """Photo-backed normalized extent of a feature tied to a statistical prior.

    ``normalized_extent`` is the feature extent divided by the same image/scene
    reference extent for which the caller wants an absolute scale. For example,
    a window occupying 0.12 of a rectified facade width may vote for facade width.
    """

    id: str = Field(min_length=1)
    cue_family: str = Field(min_length=1)
    prior_id: str = Field(min_length=1)
    normalized_extent: float = Field(gt=0, le=1)
    confidence: float = Field(default=0.8, gt=0, le=1)
    photo_index: int | None = Field(default=None, ge=1)
    observation_id: str | None = None


class ScaleCueVote(BaseModel):
    cue_id: str
    cue_family: str
    prior_id: str
    center_m: float = Field(gt=0)
    min_m: float = Field(gt=0)
    max_m: float = Field(gt=0)
    weight: float = Field(gt=0, le=1)


class ArchitecturalScaleEstimate(BaseModel):
    resolved: bool
    value_m: float | None = Field(default=None, gt=0)
    min_m: float | None = Field(default=None, gt=0)
    max_m: float | None = Field(default=None, gt=0)
    confidence: float = Field(ge=0, le=1)
    source: SourceInfo
    supporting_cue_ids: list[str] = Field(default_factory=list)
    rejected_cue_ids: list[str] = Field(default_factory=list)
    supporting_families: list[str] = Field(default_factory=list)
    votes: list[ScaleCueVote] = Field(default_factory=list)
    diagnostic: str

    @model_validator(mode="after")
    def validate_resolution(self) -> "ArchitecturalScaleEstimate":
        if self.source.kind is not SourceKind.INFERRED:
            raise ValueError("architectural scale estimates must use source.kind=inferred")
        metric_values = (self.value_m, self.min_m, self.max_m)
        if self.resolved:
            if any(value is None for value in metric_values):
                raise ValueError("resolved scale estimate requires value_m, min_m and max_m")
            if not self.min_m <= self.value_m <= self.max_m:
                raise ValueError("resolved scale value_m must lie inside its interval")
        elif any(value is not None for value in metric_values):
            raise ValueError("unresolved scale estimate must not expose metric values")
        return self


def _vote(cue: VisualScaleCue, prior: ArchitecturalDimensionPrior) -> ScaleCueVote:
    return ScaleCueVote(
        cue_id=cue.id,
        cue_family=cue.cue_family,
        prior_id=prior.id,
        center_m=prior.center_m / cue.normalized_extent,
        min_m=prior.min_m / cue.normalized_extent,
        max_m=prior.max_m / cue.normalized_extent,
        weight=cue.confidence * prior.confidence,
    )


def _unresolved(votes: list[ScaleCueVote], diagnostic: str) -> ArchitecturalScaleEstimate:
    return ArchitecturalScaleEstimate(
        resolved=False,
        confidence=0.0,
        source=SourceInfo(kind=SourceKind.INFERRED, confidence=0.0),
        rejected_cue_ids=[vote.cue_id for vote in votes],
        votes=votes,
        diagnostic=diagnostic,
    )


def _by_family(votes: list[ScaleCueVote]) -> dict[str, list[ScaleCueVote]]:
    grouped: dict[str, list[ScaleCueVote]] = {}
    for vote in votes:
        grouped.setdefault(vote.cue_family, []).append(vote)
    return grouped


def _family_capped_weight(votes: list[ScaleCueVote]) -> float:
    """Count confidence once per independent family, never once per repetition."""
    return sum(max(vote.weight for vote in family_votes) for family_votes in _by_family(votes).values())


def _family_center_and_weight(votes: list[ScaleCueVote]) -> tuple[float, float]:
    """Return a duplicate-invariant representative center and one capped family weight.

    Exact repeated centers are deduplicated before taking the median. This keeps a
    repeated window rhythm useful as consistency evidence without pretending each
    occurrence is an independent absolute-scale experiment.
    """
    unique_centers = sorted({vote.center_m for vote in votes})
    return float(median(unique_centers)), max(vote.weight for vote in votes)


def estimate_architectural_scale(
    cues: list[VisualScaleCue],
    priors: list[ArchitecturalDimensionPrior],
    *,
    minimum_independent_families: int = 2,
) -> ArchitecturalScaleEstimate:
    """Estimate one absolute reference extent without pretending priors are measurements.

    The estimator searches interval-consensus points and ranks them primarily by
    the number of independent cue families, then by family-capped confidence.
    Repeating correlated features in one family therefore cannot manufacture more
    independent evidence. Equally strong disjoint hypotheses remain unresolved
    instead of being averaged into a fabricated compromise.
    """
    if minimum_independent_families < 2:
        raise ValueError("minimum_independent_families must be at least 2")
    if not cues:
        return _unresolved([], "No visual scale cues were supplied.")

    prior_by_id = {prior.id: prior for prior in priors}
    if len(prior_by_id) != len(priors):
        raise ValueError("architectural prior ids must be unique")
    if len({cue.id for cue in cues}) != len(cues):
        raise ValueError("visual scale cue ids must be unique")

    missing = sorted({cue.prior_id for cue in cues if cue.prior_id not in prior_by_id})
    if missing:
        raise ValueError(f"visual scale cues reference unknown priors: {', '.join(missing)}")

    votes = [_vote(cue, prior_by_id[cue.prior_id]) for cue in cues]
    all_families = {vote.cue_family for vote in votes}
    if len(all_families) < minimum_independent_families:
        return _unresolved(
            votes,
            f"Need at least {minimum_independent_families} independent cue families; got {len(all_families)}.",
        )

    candidate_points = sorted(
        {
            point
            for vote in votes
            for point in (vote.min_m, vote.center_m, vote.max_m)
        }
    )
    hypotheses: list[tuple[int, float, float, list[ScaleCueVote]]] = []
    for point in candidate_points:
        support = [vote for vote in votes if vote.min_m <= point <= vote.max_m]
        families = {vote.cue_family for vote in support}
        if len(families) < minimum_independent_families:
            continue
        weight = _family_capped_weight(support)
        hypotheses.append((len(families), weight, point, support))

    if not hypotheses:
        return _unresolved(votes, "Independent cue families do not overlap on a defensible scale interval.")

    hypotheses.sort(key=lambda item: (item[0], item[1]), reverse=True)
    best_family_count, best_weight, best_point, best_support = hypotheses[0]
    best_ids = {vote.cue_id for vote in best_support}

    # If another disjoint hypothesis has equal family diversity and nearly equal
    # family-capped evidence weight, preserve the ambiguity instead of choosing arbitrarily.
    for family_count, weight, point, support in hypotheses[1:]:
        support_ids = {vote.cue_id for vote in support}
        if family_count != best_family_count or support_ids & best_ids:
            continue
        if weight >= best_weight * 0.9 and abs(point - best_point) > 1e-9:
            return _unresolved(votes, "Multiple disjoint scale hypotheses have comparable multi-family support.")

    interval_min = max(vote.min_m for vote in best_support)
    interval_max = min(vote.max_m for vote in best_support)
    if interval_max <= interval_min:
        return _unresolved(votes, "Best scale hypothesis has no non-zero consensus interval.")

    grouped_support = _by_family(best_support)
    family_representatives = [_family_center_and_weight(group) for group in grouped_support.values()]
    total_weight = sum(weight for _, weight in family_representatives)
    value_m = sum(center * weight for center, weight in family_representatives) / total_weight
    value_m = min(max(value_m, interval_min), interval_max)

    support_ids = [vote.cue_id for vote in best_support]
    support_id_set = set(support_ids)
    rejected_ids = [vote.cue_id for vote in votes if vote.cue_id not in support_id_set]
    families = sorted(grouped_support)
    support_fraction = len(families) / len(all_families)
    average_weight = total_weight / len(family_representatives)
    diversity_factor = min(1.0, len(families) / max(minimum_independent_families, 3))
    confidence = min(0.95, average_weight * (0.65 + 0.35 * support_fraction) * (0.75 + 0.25 * diversity_factor))

    return ArchitecturalScaleEstimate(
        resolved=True,
        value_m=value_m,
        min_m=interval_min,
        max_m=interval_max,
        confidence=confidence,
        source=SourceInfo(kind=SourceKind.INFERRED, confidence=confidence),
        supporting_cue_ids=support_ids,
        rejected_cue_ids=rejected_ids,
        supporting_families=families,
        votes=votes,
        diagnostic=(
            f"Resolved from {len(best_support)} cues across {len(families)} independent families; "
            f"family-capped weighting; rejected {len(rejected_ids)} non-consensus cue(s)."
        ),
    )
