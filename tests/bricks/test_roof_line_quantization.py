from brickhouse.bricks.roof import (
    SUPPORTED_SLOPE_FAMILIES,
    _shared_tileable_line_length,
    _tile_line,
)


def _family(family_id: str):
    return next(family for family in SUPPORTED_SLOPE_FAMILIES if family.id == family_id)


def test_family_18_odd_53_stud_line_uses_minimal_common_overhang():
    family = _family("18")

    assert _shared_tileable_line_length(53, family) == 54
    slope = _tile_line(54, "slope", family)
    ridge = _tile_line(54, "ridge")

    assert sum(span for _, _, span in slope) == 54
    assert sum(span for _, _, span in ridge) == 54
    assert {part_id for part_id, _, _ in slope} == {"BRICK_SLOPED_18_4X2"}


def test_even_family_18_line_does_not_gain_overhang():
    assert _shared_tileable_line_length(52, _family("18")) == 52


def test_ridge_exact_tiler_recovers_non_greedy_catalog_combination():
    placements = _tile_line(5, "ridge")

    assert sum(span for _, _, span in placements) == 5
    assert {span for _, _, span in placements} == {2, 3}
