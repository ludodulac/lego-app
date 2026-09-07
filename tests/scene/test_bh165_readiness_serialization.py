from brickhouse.scene.readiness import ArchitecturalReadinessBlocker


def test_blocker_is_structured_not_free_form_only():
    blocker = ArchitecturalReadinessBlocker(
        code="projection:geometry",
        source="projection",
        reason="geometry incomplete",
        object_id="volume-1",
    )
    data = blocker.model_dump()
    assert data["code"] == "projection:geometry"
    assert data["object_id"] == "volume-1"
