import pytest

from brickhouse.building import SourceKind
from brickhouse.scene.scale_estimation import (
    ArchitecturalDimensionPrior,
    ArchitecturalPriorProvenance,
    VisualScaleCue,
    estimate_architectural_scale,
)


def _prior(
    id: str,
    feature_kind: str,
    min_m: float,
    max_m: float,
    typical_m: float,
) -> ArchitecturalDimensionPrior:
    return ArchitecturalDimensionPrior(
        id=id,
        feature_kind=feature_kind,
        dimension="width",
        min_m=min_m,
        max_m=max_m,
        typical_m=typical_m,
        confidence=0.7,
        provenance=ArchitecturalPriorProvenance(
            reference="generic anonymized architectural prior",
            context="test fixture only",
        ),
    )


def test_multi_family_consensus_rejects_one_outlier_without_fabricating_measurement() -> None:
    priors = [
        _prior("window-width", "window", 1.05, 1.35, 1.20),
        _prior("door-width", "door", 0.85, 1.05, 0.95),
        _prior("bay-width", "glazed_bay", 1.55, 1.85, 1.70),
        _prior("odd-window", "window", 0.55, 0.70, 0.62),
    ]
    # First three cues vote for a reference width around 10 m. The last one is
    # an atypical opening interpretation voting near 5 m and must not dominate.
    cues = [
        VisualScaleCue(id="cue-window", cue_family="window_width", prior_id="window-width", normalized_extent=0.12),
        VisualScaleCue(id="cue-door", cue_family="door_width", prior_id="door-width", normalized_extent=0.095),
        VisualScaleCue(id="cue-bay", cue_family="glazed_bay_width", prior_id="bay-width", normalized_extent=0.17),
        VisualScaleCue(id="cue-outlier", cue_family="secondary_window_width", prior_id="odd-window", normalized_extent=0.12),
    ]

    estimate = estimate_architectural_scale(cues, priors)

    assert estimate.resolved is True
    assert estimate.source.kind is SourceKind.INFERRED
    assert 9.0 <= estimate.value_m <= 11.0
    assert estimate.min_m <= estimate.value_m <= estimate.max_m
    assert set(estimate.supporting_cue_ids) == {"cue-window", "cue-door", "cue-bay"}
    assert estimate.rejected_cue_ids == ["cue-outlier"]
    assert len(estimate.supporting_families) == 3
    assert 0 < estimate.confidence < 1


def test_one_repeated_feature_family_cannot_establish_absolute_scale() -> None:
    priors = [_prior("window-width", "window", 1.0, 1.3, 1.15)]
    cues = [
        VisualScaleCue(id="window-a", cue_family="window_width", prior_id="window-width", normalized_extent=0.11),
        VisualScaleCue(id="window-b", cue_family="window_width", prior_id="window-width", normalized_extent=0.12),
        VisualScaleCue(id="window-c", cue_family="window_width", prior_id="window-width", normalized_extent=0.10),
    ]

    estimate = estimate_architectural_scale(cues, priors)

    assert estimate.resolved is False
    assert estimate.value_m is None
    assert "independent cue families" in estimate.diagnostic


def test_conflicting_independent_families_remain_unresolved() -> None:
    priors = [
        _prior("window-width", "window", 1.0, 1.2, 1.1),
        _prior("door-width", "door", 0.9, 1.0, 0.95),
    ]
    cues = [
        VisualScaleCue(id="window", cue_family="window_width", prior_id="window-width", normalized_extent=0.10),
        VisualScaleCue(id="door", cue_family="door_width", prior_id="door-width", normalized_extent=0.19),
    ]

    estimate = estimate_architectural_scale(cues, priors)

    assert estimate.resolved is False
    assert estimate.value_m is None
    assert "do not overlap" in estimate.diagnostic


def test_equally_supported_disjoint_multi_family_hypotheses_remain_ambiguous() -> None:
    priors = [
        _prior("window-a", "window", 1.0, 1.2, 1.1),
        _prior("door-a", "door", 0.9, 1.1, 1.0),
        _prior("window-b", "window", 1.0, 1.2, 1.1),
        _prior("door-b", "door", 0.9, 1.1, 1.0),
    ]
    cues = [
        VisualScaleCue(id="a-window", cue_family="cluster_a_window", prior_id="window-a", normalized_extent=0.11),
        VisualScaleCue(id="a-door", cue_family="cluster_a_door", prior_id="door-a", normalized_extent=0.10),
        VisualScaleCue(id="b-window", cue_family="cluster_b_window", prior_id="window-b", normalized_extent=0.22),
        VisualScaleCue(id="b-door", cue_family="cluster_b_door", prior_id="door-b", normalized_extent=0.20),
    ]

    estimate = estimate_architectural_scale(cues, priors)

    assert estimate.resolved is False
    assert "Multiple disjoint scale hypotheses" in estimate.diagnostic


def test_duplicate_same_family_cues_do_not_inflate_value_or_confidence() -> None:
    priors = [
        _prior("window-width", "window", 1.0, 1.2, 1.1),
        _prior("door-width", "door", 0.8, 1.0, 0.9),
    ]
    baseline = [
        VisualScaleCue(id="window-a", cue_family="window_width", prior_id="window-width", normalized_extent=0.11),
        VisualScaleCue(id="door", cue_family="door_width", prior_id="door-width", normalized_extent=0.09),
    ]
    repeated = baseline + [
        VisualScaleCue(id=f"window-repeat-{index}", cue_family="window_width", prior_id="window-width", normalized_extent=0.11)
        for index in range(12)
    ]

    one = estimate_architectural_scale(baseline, priors)
    many = estimate_architectural_scale(repeated, priors)

    assert one.resolved is True and many.resolved is True
    assert many.value_m == pytest.approx(one.value_m)
    assert many.min_m == pytest.approx(one.min_m)
    assert many.max_m == pytest.approx(one.max_m)
    assert many.confidence == pytest.approx(one.confidence)
    assert len(many.supporting_cue_ids) > len(one.supporting_cue_ids)
    assert "family-capped weighting" in many.diagnostic


def test_distinct_family_adds_confidence_but_same_family_repeat_does_not() -> None:
    priors = [
        _prior("window-width", "window", 1.0, 1.2, 1.1),
        _prior("door-width", "door", 0.8, 1.0, 0.9),
        _prior("bay-width", "glazed_bay", 1.5, 1.8, 1.65),
    ]
    two_family = [
        VisualScaleCue(id="window", cue_family="window_width", prior_id="window-width", normalized_extent=0.11),
        VisualScaleCue(id="door", cue_family="door_width", prior_id="door-width", normalized_extent=0.09),
    ]
    repeated = two_family + [
        VisualScaleCue(id="window-b", cue_family="window_width", prior_id="window-width", normalized_extent=0.11),
    ]
    three_family = two_family + [
        VisualScaleCue(id="bay", cue_family="glazed_bay_width", prior_id="bay-width", normalized_extent=0.165),
    ]

    base = estimate_architectural_scale(two_family, priors)
    repeat = estimate_architectural_scale(repeated, priors)
    diverse = estimate_architectural_scale(three_family, priors)

    assert repeat.confidence == pytest.approx(base.confidence)
    assert diverse.confidence > base.confidence


def test_many_repeated_windows_cannot_rescue_a_conflicting_door_family() -> None:
    priors = [
        _prior("window-width", "window", 1.0, 1.2, 1.1),
        _prior("door-width", "door", 0.8, 1.0, 0.9),
    ]
    cues = [
        VisualScaleCue(id=f"window-{index}", cue_family="window_width", prior_id="window-width", normalized_extent=0.11)
        for index in range(20)
    ] + [
        VisualScaleCue(id="door", cue_family="door_width", prior_id="door-width", normalized_extent=0.18)
    ]

    estimate = estimate_architectural_scale(cues, priors)

    assert estimate.resolved is False
    assert "do not overlap" in estimate.diagnostic


def test_unknown_prior_reference_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown priors"):
        estimate_architectural_scale(
            [VisualScaleCue(id="cue", cue_family="door", prior_id="missing", normalized_extent=0.1)],
            [],
        )
