from pathlib import Path

import pytest

from lego_geometry_engine import (
    AABB,
    Connector,
    LDrawLibrary,
    PartDefinition,
    Transform,
    instantiate,
)
from lego_geometry_engine.assembly import analyze_assembly as analyze_with_broad_phase
from lego_geometry_engine.core import analyze_assembly as analyze_reference

FIXTURE = Path(__file__).parent / "fixtures" / "ldraw"


def _signature(report):
    def pair(item):
        return tuple(sorted((item["part_a"], item["part_b"])))

    return {
        "valid": report.valid,
        "collisions": sorted(pair(item) for item in report.collisions),
        "contacts": sorted(pair(item) for item in report.contacts),
        "connections": sorted(pair(item) for item in report.connections),
        "unsupported": sorted(report.unsupported_parts),
        "components": sorted(tuple(component) for component in report.disconnected_components),
    }


def _box_definition(part_id: str, *, connectors=()) -> PartDefinition:
    p000 = (0.0, 0.0, 0.0)
    p001 = (0.0, 0.0, 10.0)
    p010 = (0.0, 10.0, 0.0)
    p011 = (0.0, 10.0, 10.0)
    p100 = (10.0, 0.0, 0.0)
    p101 = (10.0, 0.0, 10.0)
    p110 = (10.0, 10.0, 0.0)
    p111 = (10.0, 10.0, 10.0)
    triangles = (
        (p000, p100, p110),
        (p000, p110, p010),
        (p001, p011, p111),
        (p001, p111, p101),
        (p000, p001, p101),
        (p000, p101, p100),
        (p010, p110, p111),
        (p010, p111, p011),
        (p000, p010, p011),
        (p000, p011, p001),
        (p100, p101, p111),
        (p100, p111, p110),
    )
    return PartDefinition(
        part_id,
        triangles,
        AABB((0.0, 0.0, 0.0), (10.0, 10.0, 10.0)),
        connectors=tuple(connectors),
    )


def test_broad_phase_preserves_reference_assembly_semantics():
    brick = LDrawLibrary(FIXTURE).load_part("3005")
    parts = [
        instantiate(brick, "ground"),
        instantiate(brick, "stacked", Transform.translation(0, -24, 0)),
        instantiate(brick, "floating", Transform.translation(80, -48, 0)),
        instantiate(brick, "collision-a", Transform.translation(160, 0, 0)),
        instantiate(brick, "collision-b", Transform.translation(160, 0, 0)),
    ]
    assert _signature(analyze_with_broad_phase(parts)) == _signature(analyze_reference(parts))


def test_connector_only_pair_preserves_reference_assembly_semantics():
    stud = Connector(
        "stud",
        (15.0, 5.0, 5.0),
        (1.0, 0.0, 0.0),
        ("anti_stud",),
        0.5,
    )
    anti_stud = Connector(
        "anti_stud",
        (-5.0, 5.0, 5.0),
        (-1.0, 0.0, 0.0),
        ("stud",),
        0.5,
    )
    left = instantiate(_box_definition("left", connectors=(stud,)), "left")
    right = instantiate(
        _box_definition("right", connectors=(anti_stud,)),
        "right",
        Transform.translation(20.0, 0.0, 0.0),
    )

    assert left.bbox.maximum[0] < right.bbox.minimum[0]
    optimized = analyze_with_broad_phase([left, right])
    reference = analyze_reference([left, right])
    assert _signature(optimized) == _signature(reference)
    assert optimized.connections


def test_assembly_rejects_duplicate_instance_ids():
    brick = LDrawLibrary(FIXTURE).load_part("3005")
    parts = [
        instantiate(brick, "duplicate"),
        instantiate(brick, "duplicate", Transform.translation(40, 0, 0)),
    ]

    with pytest.raises(ValueError, match="instance_id values must be unique"):
        analyze_with_broad_phase(parts)
