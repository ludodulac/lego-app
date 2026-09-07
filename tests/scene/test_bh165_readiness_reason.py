from brickhouse.scene.readiness import ArchitecturalReadinessBlocker


def test_required_input_blocker_can_name_exact_missing_field():
    blocker = ArchitecturalReadinessBlocker(
        code="required_input:metric_needed",
        source="required_input",
        reason="metric_needed",
        object_id="volume-1",
        field="width",
    )
    assert blocker.object_id == "volume-1"
    assert blocker.field == "width"
