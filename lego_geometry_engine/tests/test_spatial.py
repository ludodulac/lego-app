from __future__ import annotations

from lego_geometry_engine import AABB, PartDefinition, Transform, instantiate
from lego_geometry_engine.spatial import candidate_pairs


def _box_definition() -> PartDefinition:
    p000=(0.0,0.0,0.0); p001=(0.0,0.0,10.0); p010=(0.0,10.0,0.0); p011=(0.0,10.0,10.0)
    p100=(10.0,0.0,0.0); p101=(10.0,0.0,10.0); p110=(10.0,10.0,0.0); p111=(10.0,10.0,10.0)
    triangles=((p000,p100,p110),(p000,p110,p010),(p001,p011,p111),(p001,p111,p101),(p000,p001,p101),(p000,p101,p100),(p010,p110,p111),(p010,p111,p011),(p000,p010,p011),(p000,p011,p001),(p100,p101,p111),(p100,p111,p110))
    return PartDefinition("broad-phase-box", triangles, AABB((0.0,0.0,0.0),(10.0,10.0,10.0)))


BOX = _box_definition()


def _instance(part_id: str, x: float, y: float = 0.0, z: float = 0.0):
    return instantiate(BOX, part_id, Transform.translation(x, y, z))


def _ids(pairs):
    return {frozenset((a.instance_id, b.instance_id)) for a, b in pairs}


def test_sweep_and_prune_keeps_overlapping_and_touching_aabbs():
    parts=[_instance("a",0),_instance("touch",10),_instance("overlap",5),_instance("far",100)]
    pairs=_ids(candidate_pairs(parts))
    assert frozenset(("a","touch")) in pairs
    assert frozenset(("a","overlap")) in pairs
    assert frozenset(("a","far")) not in pairs


def test_sweep_and_prune_rejects_y_and_z_separation():
    assert list(candidate_pairs([_instance("origin",0),_instance("far-y",0,50),_instance("far-z",0,0,50)])) == []


def test_sparse_line_does_not_degenerate_to_all_pairs():
    parts=[_instance(str(index),index*40.0) for index in range(500)]
    assert list(candidate_pairs(parts)) == []


def test_candidate_pairs_are_unique():
    parts=[_instance("a",0),_instance("b",5),_instance("c",8)]
    pairs=list(candidate_pairs(parts))
    assert len(pairs) == 3
    assert len(_ids(pairs)) == 3
