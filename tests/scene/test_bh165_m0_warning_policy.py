from brickhouse.scene.readiness import ArchitecturalReadinessBlocker


def test_readiness_blocker_exposes_machine_readable_source_and_code():
    blocker = ArchitecturalReadinessBlocker(
        code="m0:unsupported",
        source="m0",
        reason="unsupported representation",
    )
    assert blocker.model_dump() == {
        "code": "m0:unsupported",
        "source": "m0",
        "reason": "unsupported representation",
        "object_id": None,
        "field": None,
    }
