from __future__ import annotations

from lego_geometry_engine import AABB, Connector, PartDefinition, Transform, instantiate
from lego_geometry_engine.spatial import candidate_pairs


def _box_definition(*, connectors=()) -> PartDefinition:
    p000=(0.0,0.0,0.0); p001=(0.0,0.0,10.0); p010=(0.0,10.0,0.0); p011=(0.0,10.0,10.0)
    p100=(10.0,0.0,0.0); p101=(10.0,0.0,10.0); p110=(10.0,10.0,0.0); p111=(10.0,10.0,10.0)
    triangles=((p000,p100,p110),(p000,p110,p010),(p001,p011,p111),(p001,p111,p101),(p000,p001,p101),(p000,p101,p100),(p010,p110,p111),(p010,p111,p011),(p000,p010,p011),(p000,p011,p001),(p100,p101,p111),(p100,p111,p110))
    return PartDefinition("broad-phase-box",triangles,AABB((0.0,0.0,0.0),(10.0,10.0,10.0)),connectors=tuple(connectors))

BOX=_box_definition()

def _instance(part_id: str,x: float,y: float=0.0,z: float=0.0):
    return instantiate(BOX,part_id,Transform.translation(x,y,z))

def _ids(pairs):
    return {frozenset((a.instance_id,b.instance_id)) for a,b in pairs}

def test_sweep_and_prune_keeps_overlapping_and_touching_aabbs():
    pairs=_ids(candidate_pairs([_instance("a",0),_instance("touch",10),_instance("overlap",5),_instance("far",100)]))
    assert frozenset(("a","touch")) in pairs
    assert frozenset(("a","overlap")) in pairs
    assert frozenset(("a","far")) not in pairs

def test_sweep_and_prune_rejects_y_and_z_separation():
    assert list(candidate_pairs([_instance("origin",0),_instance("far-y",0,50),_instance("far-z",0,0,50)]))==[]

def test_sparse_line_does_not_degenerate_to_all_pairs():
    assert list(candidate_pairs([_instance(str(index),index*40.0) for index in range(500)]))==[]

def test_candidate_pairs_are_unique():
    pairs=list(candidate_pairs([_instance("a",0),_instance("b",5),_instance("c",8)]))
    assert len(pairs)==3
    assert len(_ids(pairs))==3

def test_connector_only_candidate_is_not_culled():
    stud=Connector("stud",(15.0,5.0,5.0),(1.0,0.0,0.0),("anti_stud",),0.5)
    anti=Connector("anti_stud",(-5.0,5.0,5.0),(-1.0,0.0,0.0),("stud",),0.5)
    left=instantiate(_box_definition(connectors=(stud,)),"left")
    right=instantiate(_box_definition(connectors=(anti,)),"right",Transform.translation(20.0,0.0,0.0))
    assert left.bbox.maximum[0] < right.bbox.minimum[0]
    assert _ids(candidate_pairs([left,right])) == {frozenset(("left","right"))}
