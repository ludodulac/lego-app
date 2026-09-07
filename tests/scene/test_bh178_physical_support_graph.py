from copy import deepcopy

from brickhouse.scene.physical_support import analyze_physical_support
from brickhouse.scene.topology import ArchitecturalScene


SOURCE = {"kind": "observed", "confidence": 0.9}


def _scene(*, platform=None, stair=None, secondary_volume=None, relations=None):
    volumes = [{
        "id": "main",
        "position": {"x": 0, "y": 0, "z": 0},
        "width": {"value": 10, "source": SOURCE},
        "depth": {"value": 8, "source": SOURCE},
        "height": {"value": 6, "source": SOURCE},
        "floors": 2,
        "source": SOURCE,
    }]
    if secondary_volume is not None:
        volumes.append(secondary_volume)
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "bh178-generic",
        "name": "Physical support fixture",
        "units": "m",
        "volumes": volumes,
        "platforms": [platform] if platform is not None else [],
        "stairs": [stair] if stair is not None else [],
        "relations": relations or [],
        "appearance": {},
    })


def _platform(*, x=10.0, z=2.0, host="main", supports=None):
    return {
        "id": "deck",
        "host_volume_id": host,
        "position": {"x": x, "y": 2.0, "z": z},
        "width": 3.0,
        "depth": 3.0,
        "thickness": 0.2,
        "supports": supports or [],
        "source": SOURCE,
    }


def _stair(*, start, end):
    return {
        "id": "stair",
        "start": start,
        "end": end,
        "width": 1.0,
        "source": SOURCE,
    }


def _unresolved(object_id: str, *, relation_id: str):
    return {
        "id": relation_id,
        "kind": "connects_to",
        "subject_id": object_id,
        "object_id": "main",
        "certainty": "certain",
        "geometry_status": "unresolved",
        "statement": "connection is observed but hidden metric junction remains unresolved",
    }


def test_declared_platform_host_contact_is_proven_without_mutation():
    scene = _scene(platform=_platform(x=10.0))
    before = deepcopy(scene.model_dump())

    facts, issues = analyze_physical_support(scene)

    assert scene.model_dump() == before
    fact = next(item for item in facts if item.kind == "platform_host_contact")
    assert fact.state == "proven"
    assert fact.supporter_id == "main"
    assert issues == []


def test_declared_platform_host_contradiction_is_blocker_not_hidden_offset():
    scene = _scene(
        platform=_platform(x=12.0),
        relations=[_unresolved("deck", relation_id="hidden-deck-junction")],
    )

    facts, issues = analyze_physical_support(scene)

    assert next(item for item in facts if item.kind == "platform_host_contact").state == "contradicted"
    assert any(item.code == "platform_host_contact_contradicted" and item.severity == "blocker" for item in issues)


def test_platform_post_must_be_grounded_reach_underside_and_overlap_footprint():
    good_post = {
        "id": "post-good",
        "position": {"x": 10.5, "y": 2.5, "z": 0.0},
        "width": 0.2,
        "depth": 0.2,
        "height": 1.8,
        "source": SOURCE,
    }
    bad_post = {
        "id": "post-bad",
        "position": {"x": 20.0, "y": 20.0, "z": 0.3},
        "width": 0.2,
        "depth": 0.2,
        "height": 1.5,
        "source": SOURCE,
    }
    scene = _scene(platform=_platform(supports=[good_post, bad_post]))

    facts, issues = analyze_physical_support(scene)

    by_post = {item.supporter_id: item for item in facts if item.kind == "platform_post_support"}
    assert by_post["post-good"].state == "proven"
    assert by_post["post-bad"].state == "contradicted"
    assert any(item.code == "platform_support_post_not_supporting" for item in issues)


def test_stair_endpoint_support_proves_ground_and_platform():
    scene = _scene(
        platform=_platform(x=10.0, z=2.0),
        stair=_stair(
            start={"x": 11.0, "y": 3.0, "z": 2.0},
            end={"x": 14.0, "y": 3.0, "z": 0.0},
        ),
    )

    facts, _ = analyze_physical_support(scene)

    stair_facts = {item.endpoint: item for item in facts if item.kind == "stair_endpoint_support"}
    assert stair_facts["start"].state == "proven"
    assert stair_facts["start"].supporter_id == "deck"
    assert stair_facts["end"].state == "proven"
    assert stair_facts["end"].supporter_id == "ground"


def test_one_free_raised_stair_endpoint_remains_unresolved_without_inventing_landing():
    scene = _scene(
        stair=_stair(
            start={"x": 2.0, "y": 2.0, "z": 0.0},
            end={"x": 4.0, "y": 2.0, "z": 2.0},
        ),
        relations=[_unresolved("stair", relation_id="hidden-stair-junction")],
    )

    facts, issues = analyze_physical_support(scene)

    stair_facts = {item.endpoint: item for item in facts if item.kind == "stair_endpoint_support"}
    assert stair_facts["start"].state == "proven"
    assert stair_facts["end"].state == "unresolved"
    assert stair_facts["end"].supporter_id is None
    assert issues == []


def test_resolved_platform_support_relation_requires_metric_vertical_support():
    supported = {
        "id": "upper",
        "position": {"x": 10.5, "y": 2.5, "z": 2.0},
        "width": {"value": 1.0, "source": SOURCE},
        "depth": {"value": 1.0, "source": SOURCE},
        "height": {"value": 1.0, "source": SOURCE},
        "floors": 1,
        "source": SOURCE,
    }
    relation = {
        "id": "support-1",
        "kind": "supports",
        "subject_id": "deck",
        "object_id": "upper",
        "certainty": "certain",
        "geometry_status": "resolved",
        "statement": "deck supports upper volume",
    }
    scene = _scene(platform=_platform(), secondary_volume=supported, relations=[relation])

    facts, issues = analyze_physical_support(scene)

    fact = next(item for item in facts if item.kind == "explicit_support_relation")
    assert fact.state == "proven"
    assert issues == []


def test_resolved_support_relation_contradiction_is_blocker_and_unresolved_relation_stays_unresolved():
    floating = {
        "id": "upper",
        "position": {"x": 10.5, "y": 2.5, "z": 3.0},
        "width": {"value": 1.0, "source": SOURCE},
        "depth": {"value": 1.0, "source": SOURCE},
        "height": {"value": 1.0, "source": SOURCE},
        "floors": 1,
        "source": SOURCE,
    }
    resolved = {
        "id": "support-resolved",
        "kind": "supports",
        "subject_id": "deck",
        "object_id": "upper",
        "certainty": "certain",
        "geometry_status": "resolved",
        "statement": "deck supports upper volume",
    }
    scene = _scene(platform=_platform(), secondary_volume=floating, relations=[resolved])
    facts, issues = analyze_physical_support(scene)
    assert next(item for item in facts if item.kind == "explicit_support_relation").state == "contradicted"
    assert any(item.code == "resolved_support_relation_contradicted" and item.severity == "blocker" for item in issues)

    unresolved = dict(resolved, id="support-unresolved", geometry_status="unresolved")
    scene2 = _scene(platform=_platform(), secondary_volume=floating, relations=[unresolved])
    facts2, issues2 = analyze_physical_support(scene2)
    assert next(item for item in facts2 if item.kind == "explicit_support_relation").state == "unresolved"
    assert issues2 == []


def test_support_analysis_is_deterministic():
    scene = _scene(platform=_platform())
    first = analyze_physical_support(scene)
    second = analyze_physical_support(scene)
    assert [item.model_dump() for item in first[0]] == [item.model_dump() for item in second[0]]
    assert [item.model_dump() for item in first[1]] == [item.model_dump() for item in second[1]]
