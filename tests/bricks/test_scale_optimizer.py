from pathlib import Path

from brickhouse.bricks.scale_optimizer import recommend_front_width_studs
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


def test_recommender_finds_nearby_scale_that_materially_improves_opening_grid_fit():
    recommendation = recommend_front_width_studs(
        _scale_sensitive_building(),
        preferred_front_width_studs=48,
        search_radius_studs=4,
    )

    assert recommendation.recommended_front_width_studs == 50
    assert recommendation.recommended.score_m < recommendation.baseline.score_m
    assert recommendation.improvement_fraction > 0.5
    assert recommendation.recommended.mean_opening_error_m == 0
    assert recommendation.recommended.worst_opening_error_m == 0


def test_recommendation_is_deterministic_and_stays_inside_requested_size_band():
    building = load_building_model(FIXTURE)
    first = recommend_front_width_studs(building, preferred_front_width_studs=48, search_radius_studs=3)
    second = recommend_front_width_studs(building, preferred_front_width_studs=48, search_radius_studs=3)

    assert first == second
    assert 45 <= first.recommended_front_width_studs <= 51
    assert [c.front_width_studs for c in first.candidates] == list(range(45, 52))
    assert first.recommended.score_m <= first.baseline.score_m


def test_zero_radius_preserves_explicit_fixed_scale():
    building = load_building_model(FIXTURE)
    recommendation = recommend_front_width_studs(
        building,
        preferred_front_width_studs=48,
        search_radius_studs=0,
    )
    assert recommendation.recommended_front_width_studs == 48
    assert recommendation.improvement_fraction == 0
