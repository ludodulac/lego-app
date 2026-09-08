import pytest

from brickhouse.scene.modular_priors import (
    GLASS_BLOCK_PRIOR_CATALOG_VERSION,
    GlassBlockGridPriorQuery,
    glass_block_grid_prior_v01,
)


def test_three_module_run_scales_from_nominal_blocks_and_joint_allowance() -> None:
    prior = glass_block_grid_prior_v01(
        GlassBlockGridPriorQuery(axis="width", module_count=3)
    )

    assert prior.dimension == "width"
    assert prior.min_m == pytest.approx(0.57)
    assert prior.typical_m == pytest.approx(0.59)
    assert prior.max_m == pytest.approx(0.622)
    assert prior.min_m < prior.typical_m < prior.max_m


def test_module_count_scales_dimension_without_hardcoding_one_opening() -> None:
    three = glass_block_grid_prior_v01(
        GlassBlockGridPriorQuery(axis="height", module_count=3)
    )
    four = glass_block_grid_prior_v01(
        GlassBlockGridPriorQuery(axis="height", module_count=4)
    )

    assert four.min_m - three.min_m == pytest.approx(0.19)
    assert four.typical_m > three.typical_m
    assert four.max_m > three.max_m
    assert "4-modules" in four.id


def test_catalog_is_statistical_prior_only_and_versioned() -> None:
    prior = glass_block_grid_prior_v01(
        GlassBlockGridPriorQuery(axis="width", module_count=2)
    )

    assert prior.id.startswith(GLASS_BLOCK_PRIOR_CATALOG_VERSION)
    assert prior.provenance.kind == "statistical_prior"
    assert "Seves Glassblock" in prior.provenance.reference
    assert "old formats" in prior.provenance.context
    assert 0 < prior.confidence < 0.7


def test_invalid_or_unknown_count_does_not_fabricate_a_prior() -> None:
    with pytest.raises(ValueError):
        GlassBlockGridPriorQuery(axis="width", module_count=0)

    with pytest.raises(ValueError):
        GlassBlockGridPriorQuery(axis="width", module_count=101)
