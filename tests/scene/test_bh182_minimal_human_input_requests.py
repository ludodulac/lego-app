from brickhouse.scene.human_input_requests import derive_minimal_human_input_requests
from brickhouse.scene.readiness import (
    ArchitecturalReadinessBlocker,
    ArchitecturalReadinessDiagnostic,
    ArchitecturalReadinessReport,
)
from brickhouse.scene.spatial_analysis import SpatialRelationReport


def _report(*, blockers=None, diagnostics=None):
    return ArchitecturalReadinessReport(
        ready_for_lego=not blockers,
        blockers=blockers or [],
        diagnostics=diagnostics or [],
        spatial=SpatialRelationReport(scene_id="bh182", envelopes=[], pairs=[]),
    )


def _required_blocker(object_id, field, reason):
    return ArchitecturalReadinessBlocker(
        code=f"required_input:{reason}",
        source="required_input",
        object_id=object_id,
        field=field,
        reason=reason,
    )


def test_exact_metric_request_preserves_field_and_never_invents_value():
    reason = "building_projection_requires_metric_envelope"
    report = _report(blockers=[_required_blocker("main", "width", reason)])

    requests = derive_minimal_human_input_requests(report, [{
        "object_id": "main",
        "field": "width",
        "kind": "exact_metric",
        "reason": reason,
    }])

    assert len(requests) == 1
    assert requests[0].object_id == "main"
    assert requests[0].field == "width"
    assert requests[0].kind == "exact_metric"
    assert requests[0].value is None


def test_categorical_and_exact_roof_requests_remain_distinct():
    direction_reason = "gable_construction_requires_ridge_direction"
    pitch_reason = "gable_construction_requires_exact_pitch"
    report = _report(blockers=[
        _required_blocker("roof", "ridge_direction", direction_reason),
        _required_blocker("roof", "pitch_degrees", pitch_reason),
    ])

    requests = derive_minimal_human_input_requests(report, [
        {
            "object_id": "roof",
            "field": "pitch_degrees",
            "kind": "exact_metric",
            "reason": pitch_reason,
            "known_range_degrees": {"min": 28, "max": 36},
        },
        {
            "object_id": "roof",
            "field": "ridge_direction",
            "kind": "categorical_geometry",
            "reason": direction_reason,
        },
    ])

    assert [(item.field, item.kind) for item in requests] == [
        ("pitch_degrees", "exact_metric"),
        ("ridge_direction", "categorical_geometry"),
    ]
    assert requests[0].known_range_degrees == {"min": 28.0, "max": 36.0}
    assert requests[0].value is None


def test_duplicate_required_inputs_collapse_without_changing_reason():
    reason = "building_projection_requires_metric_envelope"
    item = {
        "object_id": "main",
        "field": "height",
        "kind": "exact_metric",
        "reason": reason,
    }
    report = _report(blockers=[_required_blocker("main", "height", reason)])

    requests = derive_minimal_human_input_requests(report, [item, dict(item)])

    assert len(requests) == 1
    assert requests[0].reason == reason


def test_stale_required_input_not_in_current_readiness_is_not_requested():
    current_reason = "building_projection_requires_metric_envelope"
    report = _report(blockers=[_required_blocker("main", "width", current_reason)])

    requests = derive_minimal_human_input_requests(report, [
        {
            "object_id": "main",
            "field": "width",
            "kind": "exact_metric",
            "reason": current_reason,
        },
        {
            "object_id": "roof",
            "field": "pitch_degrees",
            "kind": "exact_metric",
            "reason": "old_stale_reason",
        },
    ])

    assert [(item.object_id, item.field) for item in requests] == [("main", "width")]


def test_unresolved_physical_support_warning_does_not_turn_into_metric_request():
    diagnostic = ArchitecturalReadinessDiagnostic(
        code="physical_support:unresolved:chimney_host_support",
        source="physical_support",
        severity="warning",
        object_id="chimney",
        reason="ownership is not uniquely provable",
    )
    report = _report(diagnostics=[diagnostic])

    assert derive_minimal_human_input_requests(report, []) == []


def test_multiple_exact_metrics_are_not_silently_collapsed_to_scale_anchor():
    reason = "building_projection_requires_metric_envelope"
    report = _report(blockers=[
        _required_blocker("main", "width", reason),
        _required_blocker("main", "depth", reason),
        _required_blocker("main", "height", reason),
    ])
    required = [
        {"object_id": "main", "field": field, "kind": "exact_metric", "reason": reason}
        for field in ("width", "depth", "height")
    ]

    requests = derive_minimal_human_input_requests(report, required)

    assert {item.field for item in requests} == {"width", "depth", "height"}
    assert all(item.kind == "exact_metric" for item in requests)
    assert not any(item.kind == "scale_anchor" for item in requests)


def test_explicit_scale_anchor_is_preserved_only_when_upstream_declares_it():
    reason = "survey_scale_requires_front_width"
    report = _report(blockers=[_required_blocker("building", "front_width", reason)])

    requests = derive_minimal_human_input_requests(report, [{
        "object_id": "building",
        "field": "front_width",
        "kind": "scale_anchor",
        "reason": reason,
    }])

    assert len(requests) == 1
    assert requests[0].kind == "scale_anchor"
    assert requests[0].field == "front_width"
    assert requests[0].value is None


def test_request_order_is_deterministic():
    reason = "building_projection_requires_metric_envelope"
    report = _report(blockers=[
        _required_blocker("b", "height", reason),
        _required_blocker("a", "width", reason),
    ])
    inputs = [
        {"object_id": "b", "field": "height", "kind": "exact_metric", "reason": reason},
        {"object_id": "a", "field": "width", "kind": "exact_metric", "reason": reason},
    ]

    first = derive_minimal_human_input_requests(report, inputs)
    second = derive_minimal_human_input_requests(report, list(reversed(inputs)))
    assert first == second
