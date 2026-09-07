from brickhouse.building import Appearance, Position3D, SourceInfo, SourceKind
from brickhouse.scene import ArchitecturalScene, PropertyValue, SceneVolume
from brickhouse.scene.readiness_api import evaluate_strict_scene_readiness


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)


def _scene(width):
    return ArchitecturalScene(
        schema_version="0.2",
        id="bh165-evaluator",
        name="Strict readiness evaluator",
        volumes=[
            SceneVolume(
                id="main",
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


def test_strict_evaluator_reports_required_metric_as_backend_blocker():
    scene = _scene(None)
    before = scene.model_dump()
    projection, required, _compatibility, readiness = evaluate_strict_scene_readiness(scene)

    assert projection.blocked is True
    assert any(item["field"] == "width" for item in required)
    assert readiness.ready_for_lego is False
    assert any(item.source == "required_input" and item.field == "width" for item in readiness.blockers)
    assert readiness.spatial.envelopes[0].geometry_known is False
    assert scene.model_dump() == before
