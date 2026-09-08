from brickhouse.scene.architectural_priors import (
    FR_OPENING_PRIOR_CATALOG_VERSION,
    OpeningPriorQuery,
    france_residential_opening_priors_v01,
)


def _by_dimension(priors, dimension):
    return next(prior for prior in priors if prior.dimension == dimension)


def test_two_leaf_window_selects_narrower_recurrent_french_catalogue_prior() -> None:
    priors = france_residential_opening_priors_v01(
        OpeningPriorQuery(semantic_type="window", leaf_count=2)
    )

    width = _by_dimension(priors, "width")
    height = _by_dimension(priors, "height")
    assert (width.min_m, width.max_m, width.typical_m) == (1.0, 1.2, 1.1)
    assert (height.min_m, height.max_m, height.typical_m) == (1.05, 1.35, 1.2)
    assert width.confidence < 0.7
    assert width.provenance.kind == "statistical_prior"
    assert FR_OPENING_PRIOR_CATALOG_VERSION in width.id
    assert FR_OPENING_PRIOR_CATALOG_VERSION in width.provenance.context


def test_unknown_window_leaf_count_broadens_range_and_reduces_confidence() -> None:
    known = france_residential_opening_priors_v01(
        OpeningPriorQuery(semantic_type="window", leaf_count=2)
    )
    unknown = france_residential_opening_priors_v01(
        OpeningPriorQuery(semantic_type="window")
    )

    known_width = _by_dimension(known, "width")
    unknown_width = _by_dimension(unknown, "width")
    assert unknown_width.min_m < known_width.min_m
    assert unknown_width.max_m >= known_width.max_m
    assert unknown_width.confidence < known_width.confidence
    assert "unknown" in unknown_width.feature_kind


def test_one_leaf_glazed_door_height_is_widened_around_catalogue_value() -> None:
    priors = france_residential_opening_priors_v01(
        OpeningPriorQuery(semantic_type="door_or_glazed_door", leaf_count=1)
    )

    height = _by_dimension(priors, "height")
    assert height.min_m < 2.15 < height.max_m
    assert height.typical_m == 2.15
    assert height.confidence < 0.5
    assert "widened" in height.provenance.context


def test_unknown_glazed_door_configuration_is_low_confidence_and_broad() -> None:
    priors = france_residential_opening_priors_v01(
        OpeningPriorQuery(semantic_type="door_or_glazed_door")
    )

    width = _by_dimension(priors, "width")
    assert width.min_m == 0.8
    assert width.max_m == 2.4
    assert width.confidence <= 0.2
    assert "unknown" in width.feature_kind


def test_catalog_provenance_never_claims_observed_or_user_measurement_authority() -> None:
    contexts = [
        OpeningPriorQuery(semantic_type="window", leaf_count=1),
        OpeningPriorQuery(semantic_type="window", leaf_count=2),
        OpeningPriorQuery(semantic_type="window"),
        OpeningPriorQuery(semantic_type="door_or_glazed_door", leaf_count=1),
        OpeningPriorQuery(semantic_type="door_or_glazed_door"),
    ]

    priors = [
        prior
        for context in contexts
        for prior in france_residential_opening_priors_v01(context)
    ]
    assert priors
    assert all(prior.provenance.kind == "statistical_prior" for prior in priors)
    assert all("renovation and older buildings may be atypical" in prior.provenance.context for prior in priors)
