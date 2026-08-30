"""Optional correctness gates against a complete official LDraw library.

These tests deliberately skip in hermetic CI. Set LDRAW_ROOT to a complete
LDraw installation to validate the reduced deterministic fixtures against the
real dependency closure without vendoring the entire library.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from lego_geometry_engine import LDrawLibrary, Relation, Transform, analyze_assembly, check_collision, instantiate


LDRAW_ROOT = os.environ.get("LDRAW_ROOT")
pytestmark = pytest.mark.skipif(not LDRAW_ROOT, reason="LDRAW_ROOT is not configured")


def _library() -> LDrawLibrary:
    assert LDRAW_ROOT is not None
    root = Path(LDRAW_ROOT)
    if not (root / "parts").is_dir() or not (root / "p").is_dir():
        pytest.fail(f"LDRAW_ROOT does not look like a complete LDraw library: {root}")
    return LDrawLibrary(root)


def test_official_window_frame_and_pane_do_not_false_collide():
    lib = _library()
    frame = instantiate(lib.load_part("60592"), "frame")
    pane = instantiate(lib.load_part("60601"), "pane")

    assert check_collision(frame, pane) is not Relation.COLLISION
    assert not analyze_assembly([frame, pane]).collisions


def test_official_window_pane_penetration_is_detected():
    lib = _library()
    frame = instantiate(lib.load_part("60592"), "frame")
    pane = instantiate(lib.load_part("60601"), "pane", Transform.translation(0, 0, 1))

    assert check_collision(frame, pane) is Relation.COLLISION
    report = analyze_assembly([frame, pane])
    assert any({item["part_a"], item["part_b"]} == {"frame", "pane"} for item in report.collisions)
