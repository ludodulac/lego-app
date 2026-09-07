from copy import deepcopy

from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene.topology import ArchitecturalScene


SOURCE = {"kind": "observed", "confidence": 0.9}


def _scene(*, contradicted_support: bool) -> ArchitecturalScene:
    supports = []
    if contradicted_support:
        # Footprint is valid so the Scene reaches the BH-180 gate, but the post is
        # neither grounded nor tall enough to meet the declared platform level.
        supports = [{
            "id": "bad-post",
            "position": {"x": 10.5, "y": 2.5, "z": 0.5},
            "width": 0.2,
            "depth": 0.2,
            "height": 1.0,
            "source": SOURCE,
        }]

    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "bh180-pipeline",
        "name": "Physical support pipeline fixture",
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
        "platforms": [{
            "id": "deck",
            "host_volume_id": "main",
            "position": {"x": 10.0, "y": 2.0, "z": 2.0},
            "width": 3.0,
            "depth": 3.0,
            "thickness": 0.2,
            "supports": supports,
            "source": SOURCE,
        }],
        "appearance": {},
    })


def _platform_parts(bundle):
    return [
        part
        for part in bundle.brick_model.parts
        if part.placement_id.startswith("scene-platform:deck:")
    ]


def test_pipeline_keeps_supported_platform_and_preserves_scene():
    scene = _scene(contradicted_support=False)
    before = deepcopy(scene.model_dump())

    bundle = run_m0_pipeline_scene(scene, front_width_studs=24)

    assert scene.model_dump() == before
    assert _platform_parts(bundle)
    assert not any(
        issue.object_id == "deck" and issue.severity == "blocker"
        for issue in bundle.fidelity_issues
    )


def test_pipeline_withholds_platform_with_contradicted_declared_support_post():
    scene = _scene(contradicted_support=True)
    before = deepcopy(scene.model_dump())

    bundle = run_m0_pipeline_scene(scene, front_width_studs=24)

    assert scene.model_dump() == before
    assert _platform_parts(bundle) == []
    assert any(
        issue.code == "platform_support_post_not_supporting"
        and issue.severity == "blocker"
        and issue.object_id == "deck"
        for issue in bundle.fidelity_issues
    )
