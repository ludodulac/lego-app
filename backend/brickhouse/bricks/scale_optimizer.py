"""Deterministic LEGO scale recommendations from measured discretization loss."""

from __future__ import annotations

from pydantic import BaseModel, Field

from brickhouse.building.models import BuildingModel

from .discretization_report import build_discretization_quality


class ScaleCandidateScore(BaseModel):
    front_width_studs: int = Field(gt=0)
    score_m: float = Field(ge=0)
    mean_opening_error_m: float = Field(ge=0)
    worst_opening_error_m: float = Field(ge=0)
    mean_all_error_m: float = Field(ge=0)
    worst_all_error_m: float = Field(ge=0)


class ScaleRecommendation(BaseModel):
    preferred_front_width_studs: int = Field(gt=0)
    recommended_front_width_studs: int = Field(gt=0)
    search_radius_studs: int = Field(ge=0)
    baseline: ScaleCandidateScore
    recommended: ScaleCandidateScore
    candidates: list[ScaleCandidateScore]
    improvement_fraction: float = Field(ge=0, le=1)


def _score_candidate(building: BuildingModel, front_width_studs: int) -> ScaleCandidateScore:
    reports = build_discretization_quality(building, front_width_studs=front_width_studs)
    errors = [error for report in reports for wall in report.walls for error in wall.errors]
    opening_errors = [error for error in errors if error.quantity.startswith("opening_")]
    all_abs = [error.absolute_error_m for error in errors]
    opening_abs = [error.absolute_error_m for error in opening_errors]

    mean_all = sum(all_abs) / len(all_abs) if all_abs else 0.0
    worst_all = max(all_abs, default=0.0)
    mean_opening = sum(opening_abs) / len(opening_abs) if opening_abs else mean_all
    worst_opening = max(opening_abs, default=worst_all)

    # Openings carry the visual identity of a facade, so their average and worst
    # rounding losses dominate the score; blank wall-span rounding still matters.
    score = 3.0 * mean_opening + 2.0 * worst_opening + mean_all
    return ScaleCandidateScore(
        front_width_studs=front_width_studs,
        score_m=score,
        mean_opening_error_m=mean_opening,
        worst_opening_error_m=worst_opening,
        mean_all_error_m=mean_all,
        worst_all_error_m=worst_all,
    )


def recommend_front_width_studs(
    building: BuildingModel,
    *,
    preferred_front_width_studs: int,
    search_radius_studs: int = 6,
) -> ScaleRecommendation:
    """Recommend a nearby model scale without silently changing a fixed request."""
    if preferred_front_width_studs <= 0:
        raise ValueError("preferred_front_width_studs must be positive")
    if search_radius_studs < 0:
        raise ValueError("search_radius_studs must be non-negative")

    lower = max(1, preferred_front_width_studs - search_radius_studs)
    upper = preferred_front_width_studs + search_radius_studs
    candidates = [_score_candidate(building, width) for width in range(lower, upper + 1)]
    baseline = next(candidate for candidate in candidates if candidate.front_width_studs == preferred_front_width_studs)
    recommended = min(
        candidates,
        key=lambda candidate: (
            candidate.score_m,
            abs(candidate.front_width_studs - preferred_front_width_studs),
            candidate.front_width_studs,
        ),
    )
    improvement = (
        max(0.0, (baseline.score_m - recommended.score_m) / baseline.score_m)
        if baseline.score_m > 0
        else 0.0
    )
    return ScaleRecommendation(
        preferred_front_width_studs=preferred_front_width_studs,
        recommended_front_width_studs=recommended.front_width_studs,
        search_radius_studs=search_radius_studs,
        baseline=baseline,
        recommended=recommended,
        candidates=candidates,
        improvement_fraction=improvement,
    )
