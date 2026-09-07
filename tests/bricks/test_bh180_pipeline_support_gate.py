from copy import deepcopy

from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene.topology import ArchitecturalScene


SOURCE = {"kind": "observed", "confidence": 0.9}


def _scene(*, contradicted_support: bool) -> ArchitecturalScene:
    volumes = [{
        "id": "main",
        "position": {"x": 0, "y": 0, "z": 0},
        "width": {"value": 10, "source": SOURCE},
        "depth": {"value": 8, "source": SOURCE},
        "height": {"value": 6, "source": SOURCE},
        "floors": 2,
        "source": SOURCE,
    }]
    relations = []
    if contradicted_support:
        volumes.append({
            "id": "upper",
            "position": {"x": 10.5, "y": 2.5, "z": 3.0},
            "width": {"value": 1.0, "source": SOURCE},
            "depth": {"value": 1.0, "source": SOURCE},
            "height": {"value": 1.0, "source": SOURCE},
            "floors": 1,
            "source": SOURCE,
        })
        relations.append({
            "id": "support",
            "kind": "supports",
            "subject_id": "deck",
            "object_id": "upper",
            "certainty": "certain",
            "geometry_status": "resolved",
            "statement": "deck supports upper volume",
        })

    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "bh180-pipeline",
        "name": "Physical support pipeline fixture",
        "units": "m",
        "volumes": volumes,
        "platforms": [{
            "id": "deck",
            "host_volume_id": "main",
            "position": {"x": 10.0, "y": 2.0, "z": 2.0},
            "width": 3.0,
            "depth": 3.0,
            "thickness": 0.2,
            "source": SOURCE,
        }],
        "relations": relations,
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


def test_pipeline_withholds_platform_whose_resolved_support_claim_is_contradicted():
    scene = _scene(contradicted_support=True)
    before = deepcopy(scene.model_dump())

    bundle = run_m0_pipeline_scene(scene, front_width_studs=24)

    assert scene.model_dump() == before
    assert _platform_parts(bundle) == []
    assert any(
        issue.code == "resolved_support_relation_contradicted"
        and issue.severity == "blocker"
        and issue.object_id == "upper"
        for issue in bundle.fidelity_issues
    )
