from brickhouse.building import Appearance, Position3D, SourceInfo, SourceKind
from brickhouse.scene import ArchitecturalScene, ProjectionResult, PropertyValue, SceneVolume
from brickhouse.scene.readiness import assess_architectural_readiness
from brickhouse.vision.compatibility import M0Compatibility


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)


def test_identical_required_inputs_are_deduplicated():
    scene = ArchitecturalScene(
        schema_version="0.2", id="dedup", name="Dedup",
        volumes=[SceneVolume(
            id="main", position=Position3D(x=0, y=0, z=0),
            width=PropertyValue(value=4, source=SOURCE),
            depth=PropertyValue(value=5, source=SOURCE),
            height=PropertyValue(value=6, source=SOURCE),
            floors=2, source=SOURCE,
        )], appearance=Appearance(),
    )
    missing = {"object_id": "main", "field": "width", "reason": "metric_needed"}
    report = assess_architectural_readiness(
        scene,
        ProjectionResult.model_construct(building=None, issues=[]),
        [missing, dict(missing)],
        M0Compatibility(buildable=True),
    )
    assert len(report.blockers) == 1
