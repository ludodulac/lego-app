import pytest

from brickhouse.bricks.facade_rhythm_fidelity import facade_rhythm_severity, measure_facade_rhythm
from brickhouse.bricks.window_anchors import AppliedWindowAnchor
from brickhouse.building.models import Facade


def _anchor(opening_id, source_x, source_w, anchored_x, anchored_w):
    return AppliedWindowAnchor(opening_id=opening_id, facade=Facade.FRONT, composition="single", assembly_id="WINDOW_FRAME_2X3", source_x_studs=source_x, source_z_bricks=1, source_width_studs=source_w, source_height_bricks=3, anchored_x_studs=anchored_x, anchored_z_bricks=1, anchored_width_studs=anchored_w, anchored_height_bricks=3)


def test_facade_rhythm_measures_margins_and_inter_window_gap() -> None:
    metric = measure_facade_rhythm([_anchor("left", 2, 3, 2, 4), _anchor("right", 9, 3, 9, 4)], wall_width_studs=16)
    assert metric is not None
    assert metric.opening_ids == ("left", "right")
    assert metric.source_segments_studs == (2, 4, 4)
    assert metric.anchored_segments_studs == (2, 3, 3)
    assert metric.max_segment_distortion == pytest.approx(1 / 16)
    assert facade_rhythm_severity(metric) == "warning"


def test_small_local_redistribution_remains_acceptable() -> None:
    metric = measure_facade_rhythm([_anchor("left", 4, 4, 5, 4), _anchor("right", 14, 4, 14, 4)], wall_width_studs=24)
    assert metric is not None
    assert metric.max_segment_distortion == pytest.approx(1 / 24)
    assert facade_rhythm_severity(metric) is None


def test_severe_rhythm_change_is_blocker() -> None:
    metric = measure_facade_rhythm([_anchor("left", 3, 3, 6, 5), _anchor("right", 14, 3, 15, 5)], wall_width_studs=24)
    assert metric is not None
    assert metric.max_segment_distortion >= 0.20
    assert facade_rhythm_severity(metric) == "blocker"


def test_changed_opening_order_is_rejected() -> None:
    with pytest.raises(ValueError, match="changed architectural opening order"):
        measure_facade_rhythm([_anchor("left", 2, 2, 8, 2), _anchor("right", 8, 2, 2, 2)], wall_width_studs=12)


def test_metric_is_deterministic_and_scale_normalized() -> None:
    small = measure_facade_rhythm([_anchor("a", 2, 2, 3, 2)], wall_width_studs=10)
    large = measure_facade_rhythm([_anchor("a", 4, 4, 6, 4)], wall_width_studs=20)
    assert small is not None and large is not None
    assert small.max_segment_distortion == large.max_segment_distortion
    assert small.mean_segment_distortion == large.mean_segment_distortion
