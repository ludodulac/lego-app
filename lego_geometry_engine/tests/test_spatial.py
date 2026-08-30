from __future__ import annotations

from lego_geometry_engine import AABB, PartDefinition, Transform, instantiate
from lego_geometry_engine.spatial import candidate_pairs


def _box_definition() -> PartDefinition:
    triangles = (((0.0, 0.0, 0.0), (10.0, 0.0, 0.0), (0.0, 10.0, 10.0)),)
    return PartDefinition("broad-phase-box", triangles, AABB((0.0, 0.0, 0.0), (10.0, 10.0, 10.0)))


def _instance(part_id: str, x: float, y: float = 0.0, z: float = 0.0):
    return instantiate(_box_definition(), part_id, Transform.translation(x, y, z))


def _ids(pairs):
    return {frozenset((a.instance_id, b.instance_id)) for a, b in pairs}


def test_sweep_and_prune_keeps_overlapping_and_touching_aabbs():
    parts = [_instance("a", 0), _instance("touch", 10), _instance("overlap", 5), _instance("far", 100)]
    pairs = _ids(candidate_pairs(parts))
    assert frozenset(("a", "touch")) in pairs
    assert frozenset(("a", "overlap")) in pairs
    assert frozenset(("a", "far")) not in pairs


def test_sweep_and_prune_rejects_y_and_z_separation():
    parts = [_instance("origin", 0), _instance("far-y", 0, 50), _instance("far-z", 0, 0, 50)]
    assert list(candidate_pairs(parts)) == []


def test_sparse_line_does_not_degenerate_to_all_pairs():
    parts = [_instance(str(index), index * 40.0) for index in range(500)]
    assert list(candidate_pairs(parts)) == []
