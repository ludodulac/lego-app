from types import SimpleNamespace

from brickhouse.building import Appearance, Position3D, SourceInfo, SourceKind
from brickhouse.scene import ArchitecturalScene, ProjectionResult, PropertyValue, SceneVolume
from brickhouse.scene.readiness import assess_architectural_readiness
from brickhouse.vision.compatibility import M0Compatibility


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)


def test_survey_error_is_preserved_as_backend_readiness_blocker():
    scene = ArchitecturalScene(
        schema_version="0.2",
        id="survey-blocker",
        name="Survey blocker",
        volumes=[SceneVolume(
            id="main",
            position=Position3D(x=0, y=0, z=0),
            width=PropertyValue(value=4, source=SOURCE),
            depth=PropertyValue(value=5, source=SOURCE),
            height=PropertyValue(value=6, source=SOURCE),
            floors=2,
            source=SOURCE,
        )],
        appearance=Appearance(),
    )
    issue = SimpleNamespace(
        severity="error",
        code="opening_mismatch",
        message="opening evidence is not preserved",
        object_id="opening-1",
    )
    report = assess_architectural_readiness(
        scene,
        ProjectionResult.model_construct(building=None, issues=[]),
        [],
        M0Compatibility(buildable=True),
        survey_issues=[issue],
    )

    assert report.ready_for_lego is False
    assert len(report.blockers) == 1
    blocker = report.blockers[0]
    assert blocker.source == "survey"
    assert blocker.code == "survey:opening_mismatch"
    assert blocker.object_id == "opening-1"
