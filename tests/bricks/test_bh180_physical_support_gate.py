from copy import deepcopy

from brickhouse.bricks.scene_physical_support_gate import evaluate_scene_physical_support_gate
from brickhouse.scene.topology import ArchitecturalScene


SOURCE = {"kind": "observed", "confidence": 0.9}


def _platform(*, supports=None):
    return {
        "id": "deck",
        "host_volume_id": "main",
        "position": {"x": 10.0, "y": 2.0, "z": 2.0},
        "width": 3.0,
        "depth": 3.0,
        "thickness": 0.2,
        "supports": supports or [],
        "source": SOURCE,
    }


def _scene(*, platform, relation=None, secondary_z=None):
    volumes = [{
        "id": "main",
        "position": {"x": 0, "y": 0, "z": 0},
        "width": {"value": 10, "source": SOURCE},
        "depth": {"value": 8, "source": SOURCE},
        "height": {"value": 6, "source": SOURCE},
        "floors": 2,
        "source": SOURCE,
    }]
    if secondary_z is not None:
        volumes.append({
            "id": "upper",
            "position": {"x": 10.5, "y": 2.5, "z": secondary_z},
            "width": {"value": 1.0, "source": SOURCE},
            "depth": {"value": 1.0, "source": SOURCE},
            "height": {"value": 1.0, "source": SOURCE},
            "floors": 1,
            "source": SOURCE,
        })
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "bh180-generic",
        "name": "Physical support production gate fixture",
        "units": "m",
        "volumes": volumes,
        "platforms": [platform],
        "relations": [relation] if relation is not None else [],
        "appearance": {},
    })


def test_supported_platform_passes_gate_without_mutation():
    good_post = {
        "id": "post",
        "position": {"x": 10.5, "y": 2.5, "z": 0.0},
        "width": 0.2,
        "depth": 0.2,
        "height": 1.8,
        "source": SOURCE,
    }
    scene = _scene(platform=_platform(supports=[good_post]))
    before = deepcopy(scene.model_dump())

    gate = evaluate_scene_physical_support_gate(scene)

    assert scene.model_dump() == before
    assert gate.blocked_platform_ids == frozenset()
    assert gate.platform_scene(scene) is scene
    assert not [issue for issue in gate.fidelity_issues if issue.severity == "blocker"]


def test_contradicted_platform_post_blocks_only_platform_augmentation():
    bad_post = {
        "id": "post-bad",
        "position": {"x": 20.0, "y": 20.0, "z": 0.5},
        "width": 0.2,
        "depth": 0.2,
        "height": 1.0,
        "source": SOURCE,
    }
    scene = _scene(platform=_platform(supports=[bad_post]))
    before = deepcopy(scene.model_dump())

    gate = evaluate_scene_physical_support_gate(scene)
    filtered = gate.platform_scene(scene)

    assert scene.model_dump() == before
    assert gate.blocked_platform_ids == frozenset({"deck"})
    assert filtered.platforms == []
    assert any(
        issue.code == "platform_support_post_not_supporting"
        and issue.severity == "blocker"
        and issue.object_id == "deck"
        for issue in gate.fidelity_issues
    )


def test_contradicted_explicit_support_blocks_supporter_not_unrelated_volume():
    relation = {
        "id": "support",
        "kind": "supports",
        "subject_id": "deck",
        "object_id": "upper",
        "certainty": "certain",
        "geometry_status": "resolved",
        "statement": "deck supports upper volume",
    }
    scene = _scene(platform=_platform(), relation=relation, secondary_z=3.0)

    gate = evaluate_scene_physical_support_gate(scene)

    assert gate.blocked_platform_ids == frozenset({"deck"})
    assert any(issue.code == "resolved_support_relation_contradicted" for issue in gate.fidelity_issues)


def test_unresolved_support_relation_is_reported_without_synthetic_blocking():
    relation = {
        "id": "support",
        "kind": "supports",
        "subject_id": "deck",
        "object_id": "upper",
        "certainty": "certain",
        "geometry_status": "unresolved",
        "statement": "support relation observed but junction hidden",
    }
    scene = _scene(platform=_platform(), relation=relation, secondary_z=3.0)

    gate = evaluate_scene_physical_support_gate(scene)

    assert gate.blocked_platform_ids == frozenset()
    assert any(
        issue.code == "physical_support_unresolved"
        and issue.severity == "warning"
        and issue.object_id == "upper"
        for issue in gate.fidelity_issues
    )


def test_gate_diagnostics_are_deterministic():
    scene = _scene(platform=_platform())
    first = evaluate_scene_physical_support_gate(scene)
    second = evaluate_scene_physical_support_gate(scene)
    assert first == second
