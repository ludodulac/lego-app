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


def _family_summary(votes: list[ScaleCueVote]) -> tuple[float, float, float, float]:
    """Return duplicate-invariant center/range/weight for one correlated family.

    Raw repeated cues are consistency samples, not independent measurements. Exact
    duplicates are removed before aggregation. With at least three genuinely
    different intervals, median bounds robustly ignore a single outlier. With one
    or two unique intervals, the union is retained because narrowing would claim
    more information than the family actually provides.
    """
    unique = sorted({(vote.center_m, vote.min_m, vote.max_m) for vote in votes})
    centers = [item[0] for item in unique]
    mins = [item[1] for item in unique]
    maxs = [item[2] for item in unique]
    center = float(median(centers))
    if len(unique) >= 3:
        min_m = float(median(mins))
        max_m = float(median(maxs))
    else:
        min_m = min(mins)
        max_m = max(maxs)
    return center, min_m, max_m, max(vote.weight for vote in votes)


def _family_summaries(votes: list[ScaleCueVote]) -> dict[str, tuple[float, float, float, float]]:
    return {family: _family_summary(group) for family, group in _by_family(votes).items()}


def estimate_architectural_scale(
    cues: list[VisualScaleCue],
    priors: list[ArchitecturalDimensionPrior],
    *,
    minimum_independent_families: int = 2,
) -> ArchitecturalScaleEstimate:
    """Estimate one absolute reference extent without pretending priors are measurements.

    Correlated repetitions are first reduced to one robust family-level hypothesis.
    Cross-family consensus therefore combines genuinely independent evidence, while
    raw votes remain available for diagnostics. Equally strong disjoint hypotheses
    remain unresolved instead of being averaged into a fabricated compromise.
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
    all_family_summaries = _family_summaries(votes)
    if len(all_family_summaries) < minimum_independent_families:
        return _unresolved(
            votes,
            f"Need at least {minimum_independent_families} independent cue families; got {len(all_family_summaries)}.",
        )

    candidate_points = sorted(
        {
            point
            for center, min_m, max_m, _ in all_family_summaries.values()
            for point in (min_m, center, max_m)
        }
    )
    hypotheses: list[tuple[int, float, float, list[str]]] = []
    for point in candidate_points:
        support_families = [
            family
            for family, (_, min_m, max_m, _) in all_family_summaries.items()
            if min_m <= point <= max_m
        ]
        if len(support_families) < minimum_independent_families:
            continue
        weight = sum(all_family_summaries[family][3] for family in support_families)
        hypotheses.append((len(support_families), weight, point, support_families))

    if not hypotheses:
        return _unresolved(votes, "Independent cue families do not overlap on a defensible scale interval.")

    hypotheses.sort(key=lambda item: (item[0], item[1]), reverse=True)
    best_family_count, best_weight, best_point, best_families = hypotheses[0]
    best_family_set = set(best_families)

    for family_count, weight, point, families in hypotheses[1:]:
        family_set = set(families)
        if family_count != best_family_count or family_set & best_family_set:
            continue
        if weight >= best_weight * 0.9 and abs(point - best_point) > 1e-9:
            return _unresolved(votes, "Multiple disjoint scale hypotheses have comparable multi-family support.")

    interval_min = max(all_family_summaries[family][1] for family in best_families)
    interval_max = min(all_family_summaries[family][2] for family in best_families)
    if interval_max <= interval_min:
        return _unresolved(votes, "Best scale hypothesis has no non-zero family-level consensus interval.")

    family_representatives = [
        (all_family_summaries[family][0], all_family_summaries[family][3])
        for family in best_families
    ]
    total_weight = sum(weight for _, weight in family_representatives)
    value_m = sum(center * weight for center, weight in family_representatives) / total_weight
    value_m = min(max(value_m, interval_min), interval_max)

    supporting_votes = [
        vote
        for vote in votes
        if vote.cue_family in best_family_set
        and vote.max_m >= interval_min
        and vote.min_m <= interval_max
    ]
    support_ids = [vote.cue_id for vote in supporting_votes]
    support_id_set = set(support_ids)
    rejected_ids = [vote.cue_id for vote in votes if vote.cue_id not in support_id_set]
    families = sorted(best_families)
    support_fraction = len(families) / len(all_family_summaries)
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
            f"Resolved from {len(support_ids)} cues across {len(families)} independent families; "
            f"uncertainty aggregated at family level; rejected {len(rejected_ids)} non-consensus cue(s)."
        ),
    )
