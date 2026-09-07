from brickhouse.building import Appearance, Position3D, SourceInfo, SourceKind
from brickhouse.scene import ArchitecturalScene, ProjectionIssue, ProjectionResult, ProjectionSeverity, PropertyValue, SceneVolume
from brickhouse.scene.readiness import assess_architectural_readiness
from brickhouse.vision.compatibility import M0Compatibility


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)


def _scene(width=4.0):
    return ArchitecturalScene(
        schema_version="0.2",
        id="bh165-generic",
        name="Generic readiness scene",
        volumes=[
            SceneVolume(
                id="house",
                position=Position3D(x=0, y=0, z=0),
                width=PropertyValue(value=width, source=SOURCE),
                depth=PropertyValue(value=5, source=SOURCE),
                height=PropertyValue(value=6, source=SOURCE),
                floors=2,
                source=SOURCE,
            )
        ],
        appearance=Appearance(),
    )


def _projection(*issues):
    return ProjectionResult.model_construct(building=None, issues=list(issues))


def test_complete_backend_diagnostics_are_ready_and_include_spatial_evidence():
    scene = _scene()
    before = scene.model_dump()
    report = assess_architectural_readiness(
        scene,
        _projection(),
        [],
        M0Compatibility(buildable=True),
    )

    assert report.ready_for_lego is True
    assert report.blockers == []
    assert report.spatial.envelopes[0].geometry_known is True
    assert scene.model_dump() == before


def test_projection_required_input_and_m0_blockers_are_all_preserved():
    scene = _scene()
    projection = _projection(
        ProjectionIssue(
            code="volume_geometry_incomplete",
            severity=ProjectionSeverity.BLOCKER,
            message="volume needs width",
            object_id="house",
        )
    )
    report = assess_architectural_readiness(
        scene,
        projection,
        [
            {
                "object_id": "house",
                "field": "width",
                "kind": "exact_metric",
                "reason": "building_projection_requires_metric_envelope",
            }
        ],
        M0Compatibility(buildable=False, blockers=["unsupported downstream representation"]),
    )

    assert report.ready_for_lego is False
    assert {item.source for item in report.blockers} == {"projection", "required_input", "m0"}
    assert any(item.object_id == "house" and item.field == "width" for item in report.blockers)


def test_unknown_spatial_envelope_is_diagnostic_not_automatically_blocking():
    scene = _scene(width=None)
    report = assess_architectural_readiness(
        scene,
        _projection(),
        [],
        M0Compatibility(buildable=True),
    )

    assert report.ready_for_lego is True
    assert report.spatial.envelopes[0].geometry_known is False


def test_blocker_order_is_deterministic_not_producer_order_dependent():
    scene = _scene()
    first = ProjectionIssue(
        code="z-last",
        severity=ProjectionSeverity.BLOCKER,
        message="z",
        object_id="z",
    )
    second = ProjectionIssue(
        code="a-first",
        severity=ProjectionSeverity.BLOCKER,
        message="a",
        object_id="a",
    )
    one = assess_architectural_readiness(
        scene, _projection(first, second), [], M0Compatibility(buildable=True)
    ).model_dump()
    two = assess_architectural_readiness(
        scene, _projection(second, first), [], M0Compatibility(buildable=True)
    ).model_dump()

    assert one == two
