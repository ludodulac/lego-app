from types import SimpleNamespace

from brickhouse.bricks.facade_rhythm_export import facade_rhythm_fidelity_issues
from brickhouse.bricks.window_anchors import AppliedWindowAnchor
from brickhouse.building.models import Facade


def _anchor(opening_id, source_x, source_w, anchored_x, anchored_w):
    return AppliedWindowAnchor(
        opening_id=opening_id,
        facade=Facade.FRONT,
        composition="single",
        assembly_id="WINDOW_FRAME_2X3",
        source_x_studs=source_x,
        source_z_bricks=1,
        source_width_studs=source_w,
        source_height_bricks=3,
        anchored_x_studs=anchored_x,
        anchored_z_bricks=1,
        anchored_width_studs=anchored_w,
        anchored_height_bricks=3,
    )


def _application(anchors, width=24):
    wall = SimpleNamespace(facade=Facade.FRONT, grid=SimpleNamespace(width_studs=width))
    return SimpleNamespace(anchors=anchors, shell=SimpleNamespace(walls=[wall]))


def test_severe_facade_rhythm_distortion_becomes_export_blocker():
    issues = facade_rhythm_fidelity_issues(_application([
        _anchor("left", 3, 3, 6, 5),
        _anchor("right", 14, 3, 15, 5),
    ]))
    assert len(issues) == 1
    assert issues[0].code == "lego_facade_rhythm_distortion"
    assert issues[0].severity == "blocker"
    assert issues[0].object_id == "facade:front"
    assert "left, right" in issues[0].message


def test_acceptable_local_redistribution_emits_no_issue():
    issues = facade_rhythm_fidelity_issues(_application([
        _anchor("left", 4, 4, 5, 4),
        _anchor("right", 14, 4, 14, 4),
    ]))
    assert issues == []
