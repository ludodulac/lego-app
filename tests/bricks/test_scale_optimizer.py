from pathlib import Path

from brickhouse.bricks.scale_optimizer import (
    VOLUME_PROPORTION_TOLERANCE,
    ScaleCandidateScore,
    recommend_front_width_studs,
)
from brickhouse.building.validation import load_building_model


FIXTURE = Path("docs/examples/building-model-simple-house.json")


def _scale_sensitive_building():
    building = load_building_model(FIXTURE)
    opening = building.openings[0].model_copy(update={
        "offset_horizontal": 1.4,
        "offset_vertical": 1.2,
        "width": 1.4,
        "height": 1.2,
    })
    return building.model_copy(update={"openings": [opening]})


def test_recommender_finds_nearby_scale_without_sacrificing_global_proportions():
    recommendation = recommend_front_width_studs(
        _scale_sensitive_building(),
        preferred_front_width_studs=48,
        search_radius_studs=4,
    )

    best_proportion_error = min(c.worst_volume_proportion_error for c in recommendation.candidates)
    assert recommendation.recommended.worst_volume_proportion_error <= (
        best_proportion_error + VOLUME_PROPORTION_TOLERANCE
    )
    safe = [
        c for c in recommendation.candidates
        if c.worst_volume_proportion_error <= best_proportion_error + VOLUME_PROPORTION_TOLERANCE
    ]
    assert recommendation.recommended.score_m == min(c.score_m for c in safe)
    assert recommendation.recommended.score_m <= recommendation.baseline.score_m


def test_scale_candidate_records_global_proportion_error():
    recommendation = recommend_front_width_studs(
        _scale_sensitive_building(), preferred_front_width_studs=48, search_radius_studs=1
    )
    assert all(candidate.worst_volume_proportion_error >= 0 for candidate in recommendation.candidates)
    assert isinstance(recommendation.recommended, ScaleCandidateScore)


def test_recommendation_is_deterministic_and_stays_inside_requested_size_band():
    building = load_building_model(FIXTURE)
    first = recommend_front_width_studs(building, preferred_front_width_studs=48, search_radius_studs=3)
    second = recommend_front_width_studs(building, preferred_front_width_studs=48, search_radius_studs=3)

    assert first == second
    assert 45 <= first.recommended_front_width_studs <= 51
    assert [c.front_width_studs for c in first.candidates] == list(range(45, 52))
    best_proportion_error = min(c.worst_volume_proportion_error for c in first.candidates)
    assert first.recommended.worst_volume_proportion_error <= (
        best_proportion_error + VOLUME_PROPORTION_TOLERANCE
    )


def test_zero_radius_preserves_explicit_fixed_scale():
    building = load_building_model(FIXTURE)
    recommendation = recommend_front_width_studs(
        building,
        preferred_front_width_studs=48,
        search_radius_studs=0,
    )
    assert recommendation.recommended_front_width_studs == 48
    assert recommendation.improvement_fraction == 0
