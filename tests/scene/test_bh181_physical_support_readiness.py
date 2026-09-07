from copy import deepcopy

from brickhouse.scene.projection import ProjectionResult
from brickhouse.scene.readiness import assess_architectural_readiness
from brickhouse.scene.topology import ArchitecturalScene


SOURCE = {"kind": "observed", "confidence": 0.9}


def _report(scene):
    return assess_architectural_readiness(
        scene,
        ProjectionResult(building=None, issues=[]),
        [],
        None,
    )


def _scene(*, platform=None, roof=None, chimney=None):
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "bh181-generic",
        "name": "Physical support readiness fixture",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE},
            "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "platforms": [platform] if platform is not None else [],
        "roofs": [roof] if roof is not None else [],
        "chimneys": [chimney] if chimney is not None else [],
        "appearance": {},
    })


def _platform(*, x=10.0, supports=None):
    return {
        "id": "deck",
        "host_volume_id": "main",
        "position": {"x": x, "y": 2.0, "z": 2.0},
        "width": 3.0,
        "depth": 3.0,
        "thickness": 0.2,
        "supports": supports or [],
        "source": SOURCE,
    }


def test_supported_scene_remains_ready_and_non_mutating():
    post = {
        "id": "post",
        "position": {"x": 10.5, "y": 2.5, "z": 0.0},
        "width": 0.2,
        "depth": 0.2,
        "height": 2.0,
        "source": SOURCE,
    }
    scene = _scene(platform=_platform(supports=[post]))
    before = deepcopy(scene.model_dump())

    report = _report(scene)

    assert scene.model_dump() == before
    assert report.ready_for_lego is True
    assert not [item for item in report.blockers if item.source == "physical_support"]


def test_contradicted_support_is_strict_readiness_blocker():
    bad_post = {
        "id": "bad-post",
        "position": {"x": 10.5, "y": 2.5, "z": 0.5},
        "width": 0.2,
        "depth": 0.2,
        "height": 1.0,
        "source": SOURCE,
    }
    report = _report(_scene(platform=_platform(supports=[bad_post])))

    assert report.ready_for_lego is False
    assert any(
        item.code == "physical_support:platform_support_post_not_supporting"
        and item.source == "physical_support"
        and item.object_id == "deck"
        for item in report.blockers
    )


def test_unresolved_host_association_is_warning_not_invented_blocker():
    report = _report(_scene(platform=_platform(x=12.0)))

    assert report.ready_for_lego is True
    assert not [item for item in report.blockers if item.source == "physical_support"]
    assert any(
        item.code == "physical_support:unresolved:platform_host_contact"
        and item.object_id == "deck"
        for item in report.diagnostics
    )


def test_neighboring_context_chimney_ownership_stays_unresolved_not_blocked():
    roof = {
        "id": "roof",
        "volume_id": "main",
        "type": "gable",
        "overhang": 0.0,
        "source": SOURCE,
    }
    chimney = {
        "id": "context-chimney",
        "position": {"x": 20.0, "y": 2.0, "z": 5.0},
        "width": 0.8,
        "depth": 0.8,
        "height": 3.0,
        "source": SOURCE,
    }

    report = _report(_scene(roof=roof, chimney=chimney))

    assert report.ready_for_lego is True
    assert not [item for item in report.blockers if item.object_id == "context-chimney"]
    assert any(
        item.code == "physical_support:unresolved:chimney_host_support"
        and item.object_id == "context-chimney"
        for item in report.diagnostics
    )


def test_physical_support_readiness_is_deterministic():
    scene = _scene(platform=_platform(x=12.0))
    first = _report(scene)
    second = _report(scene)
    assert first == second
