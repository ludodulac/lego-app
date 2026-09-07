from brickhouse.building import Appearance, Position3D, SourceInfo, SourceKind
from brickhouse.scene import ArchitecturalScene, ProjectionResult, PropertyValue, SceneVolume
from brickhouse.scene.readiness import assess_architectural_readiness
from brickhouse.vision.compatibility import M0Compatibility


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)


def test_spatial_unknown_becomes_blocking_only_through_required_input():
    scene = ArchitecturalScene(
        schema_version="0.2", id="spatial-policy", name="Spatial policy",
        volumes=[SceneVolume(
            id="main", position=Position3D(x=0, y=0, z=0),
            width=PropertyValue(value=None, source=SOURCE),
            depth=PropertyValue(value=5, source=SOURCE),
            height=PropertyValue(value=6, source=SOURCE),
            floors=2, source=SOURCE,
        )], appearance=Appearance(),
    )
    projection = ProjectionResult.model_construct(building=None, issues=[])
    diagnostic = assess_architectural_readiness(
        scene, projection, [], M0Compatibility(buildable=True)
    )
    required = assess_architectural_readiness(
        scene,
        projection,
        [{"object_id": "main", "field": "width", "reason": "metric_needed"}],
        M0Compatibility(buildable=True),
    )

    assert diagnostic.spatial.envelopes[0].geometry_known is False
    assert diagnostic.ready_for_lego is True
    assert required.ready_for_lego is False
