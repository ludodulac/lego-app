from brickhouse.scene.readiness import ArchitecturalReadinessReport
from brickhouse.scene.spatial_analysis import SpatialRelationReport


def test_readiness_decision_is_explicit_boolean():
    report = ArchitecturalReadinessReport(
        ready_for_lego=False,
        spatial=SpatialRelationReport(scene_id="scene", envelopes=[], pairs=[]),
    )
    assert report.ready_for_lego is False
