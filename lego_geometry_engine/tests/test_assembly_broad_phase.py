from pathlib import Path

from lego_geometry_engine import LDrawLibrary, Transform, instantiate
from lego_geometry_engine.assembly import analyze_assembly as analyze_with_broad_phase
from lego_geometry_engine.core import analyze_assembly as analyze_reference


FIXTURE = Path(__file__).parent / "fixtures" / "ldraw"


def _signature(report):
    # Pair ordering is an implementation detail; normalize it before comparing.
    pair = lambda item: tuple(sorted((item["part_a"], item["part_b"])))
    return {
        "valid": report.valid,
        "collisions": sorted(pair(item) for item in report.collisions),
        "contacts": sorted(pair(item) for item in report.contacts),
        "connections": sorted((*pair(item), item["type"]) for item in report.connections),
        "unsupported": sorted(report.unsupported_parts),
        "components": sorted(tuple(component) for component in report.disconnected_components),
    }


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
