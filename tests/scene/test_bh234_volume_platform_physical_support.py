from brickhouse.scene import ArchitecturalScene
from brickhouse.scene.physical_support import analyze_physical_support

SOURCE = {"kind": "observed", "confidence": 0.9}


def _payload() -> dict:
    return {
        "schema_version": "0.2",
        "id": "bh234-volume-platform",
        "name": "Directional volume support fixture",
        "units": "m",
        "volumes": [{
            "id": "bearing-volume",
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "width": {"value": 3.0, "source": SOURCE},
            "depth": {"value": 3.0, "source": SOURCE},
            "height": {"value": 2.0, "source": SOURCE},
            "floors": 1,
            "source": SOURCE,
        }],
        "platforms": [{
            "id": "landing",
            "host_volume_id": "bearing-volume",
            "position": {"x": 0.5, "y": 0.5, "z": 2.0},
            "width": 2.0,
            "depth": 2.0,
            "thickness": 0.2,
            "source": SOURCE,
        }],
        "relations": [{
            "id": "bearing-volume-supports-landing",
            "kind": "supports",
            "subject_id": "bearing-volume",
            "object_id": "landing",
            "certainty": "certain",
            "geometry_status": "resolved",
            "statement": "bearing volume supports landing",
        }],
        "appearance": {},
    }


def _explicit_support_fact(scene):
    facts, issues = analyze_physical_support(scene)
    fact = next(item for item in facts if item.kind == "explicit_support_relation")
    return fact, issues


def test_resolved_volume_supports_platform_is_proven_when_bearing_geometry_matches():
    scene = ArchitecturalScene.model_validate(_payload())

    fact, issues = _explicit_support_fact(scene)

    assert fact.supporter_id == "bearing-volume"
    assert fact.object_id == "landing"
    assert fact.state == "proven"
    assert issues == []


def test_resolved_volume_supports_platform_contradiction_remains_blocking():
    scene = ArchitecturalScene.model_validate(_payload())
    # Simulate a post-validation geometry drift to exercise the physical-support
    # consumer directly. Canonical Scene validation rejects this shape earlier.
    scene.platforms[0].position.z = 2.5

    fact, issues = _explicit_support_fact(scene)

    assert fact.state == "contradicted"
    assert any(
        issue.code == "resolved_support_relation_contradicted"
        and issue.severity == "blocker"
        and issue.object_id == "landing"
        for issue in issues
    )
