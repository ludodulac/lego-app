from copy import deepcopy

from brickhouse.scene.physical_support import analyze_physical_support
from brickhouse.scene.topology import ArchitecturalScene


SOURCE = {"kind": "observed", "confidence": 0.9}


def _scene(*, roof_type="flat", pitch=None, chimney=None, relation=None, complete_host=True):
    height_value = 6 if complete_host else None
    roof = {
        "id": "roof",
        "volume_id": "main",
        "type": roof_type,
        "overhang": 0.0,
        "source": SOURCE,
    }
    if pitch is not None:
        roof["pitch_degrees"] = pitch
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "bh179-generic",
        "name": "Roof chimney support fixture",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE},
            "depth": {"value": 8, "source": SOURCE},
            "height": {"value": height_value, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "roofs": [roof],
        "chimneys": [chimney] if chimney is not None else [],
        "relations": [relation] if relation is not None else [],
        "appearance": {},
    })


def _chimney(*, x=4.0, y=3.0, z=5.0, height=3.0):
    return {
        "id": "chimney",
        "position": {"x": x, "y": y, "z": z},
        "width": 0.8,
        "depth": 0.8,
        "height": height,
        "source": SOURCE,
    }


def test_roof_support_is_proven_from_explicit_metric_host_without_choosing_pitch():
    scene = _scene(roof_type="gable", chimney=None)
    before = deepcopy(scene.model_dump())

    facts, issues = analyze_physical_support(scene)

    assert scene.model_dump() == before
    roof_fact = next(item for item in facts if item.kind == "roof_host_support")
    assert roof_fact.state == "proven"
    assert roof_fact.supporter_id == "main"
    assert scene.roofs[0].pitch_degrees is None
    assert scene.roofs[0].ridge_direction is None
    assert issues == []


def test_roof_support_stays_unresolved_when_host_height_is_unknown():
    scene = _scene(roof_type="gable", complete_host=False)

    facts, issues = analyze_physical_support(scene)

    roof_fact = next(item for item in facts if item.kind == "roof_host_support")
    assert roof_fact.state == "unresolved"
    assert issues == []


def test_flat_roof_chimney_support_is_proven_by_footprint_and_vertical_crossing():
    scene = _scene(chimney=_chimney())

    facts, issues = analyze_physical_support(scene)

    chimney_fact = next(item for item in facts if item.kind == "chimney_host_support")
    assert chimney_fact.state == "proven"
    assert chimney_fact.supporter_id == "roof"
    assert issues == []


def test_pitched_roof_chimney_stays_unresolved_without_constructible_roof_plane():
    scene = _scene(roof_type="gable", chimney=_chimney())

    facts, issues = analyze_physical_support(scene)

    chimney_fact = next(item for item in facts if item.kind == "chimney_host_support")
    assert chimney_fact.state == "unresolved"
    assert chimney_fact.supporter_id is None
    assert issues == []


def test_resolved_roof_support_claim_for_nonintersecting_chimney_is_blocker():
    relation = {
        "id": "roof-supports-chimney",
        "kind": "supports",
        "subject_id": "roof",
        "object_id": "chimney",
        "certainty": "certain",
        "geometry_status": "resolved",
        "statement": "roof supports chimney",
    }
    scene = _scene(chimney=_chimney(x=20.0), relation=relation)

    facts, issues = analyze_physical_support(scene)

    explicit = next(item for item in facts if item.kind == "explicit_support_relation")
    assert explicit.state == "contradicted"
    assert any(
        item.code == "resolved_support_relation_contradicted"
        and item.severity == "blocker"
        and item.object_id == "chimney"
        for item in issues
    )


def test_unresolved_roof_support_relation_does_not_invent_contact():
    relation = {
        "id": "roof-supports-chimney",
        "kind": "supports",
        "subject_id": "roof",
        "object_id": "chimney",
        "certainty": "certain",
        "geometry_status": "unresolved",
        "statement": "roof support is observed but exact junction is hidden",
    }
    scene = _scene(roof_type="gable", chimney=_chimney(), relation=relation)

    facts, issues = analyze_physical_support(scene)

    explicit = next(item for item in facts if item.kind == "explicit_support_relation")
    assert explicit.state == "unresolved"
    assert issues == []


def test_roof_chimney_support_analysis_is_deterministic():
    scene = _scene(chimney=_chimney())
    first = analyze_physical_support(scene)
    second = analyze_physical_support(scene)
    assert [item.model_dump() for item in first[0]] == [item.model_dump() for item in second[0]]
    assert [item.model_dump() for item in first[1]] == [item.model_dump() for item in second[1]]
