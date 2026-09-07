from brickhouse.building import Appearance, Position3D, SourceInfo, SourceKind
from brickhouse.scene import ArchitecturalScene, ProjectionIssue, ProjectionResult, ProjectionSeverity, PropertyValue, SceneVolume
from brickhouse.scene.readiness import assess_architectural_readiness
from brickhouse.vision.compatibility import M0Compatibility


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)


def test_nonblocking_diagnostics_do_not_make_ci_or_build_readiness_overstrict():
    scene = ArchitecturalScene(
        schema_version="0.2", id="warning", name="Warning",
        volumes=[SceneVolume(
            id="main", position=Position3D(x=0, y=0, z=0),
            width=PropertyValue(value=4, source=SOURCE), depth=PropertyValue(value=5, source=SOURCE),
            height=PropertyValue(value=6, source=SOURCE), floors=2, source=SOURCE,
        )], appearance=Appearance(),
    )
    projection = ProjectionResult.model_construct(
        building=None,
        issues=[ProjectionIssue(code="detail_warning", severity=ProjectionSeverity.WARNING, message="detail")],
    )
    report = assess_architectural_readiness(
        scene, projection, [], M0Compatibility(buildable=True, warnings=["detail"])
    )
    assert report.ready_for_lego is True
    assert report.blockers == []
