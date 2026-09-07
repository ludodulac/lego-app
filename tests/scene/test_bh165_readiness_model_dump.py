from brickhouse.scene.readiness import ArchitecturalReadinessReport
from brickhouse.scene.spatial_analysis import SpatialRelationReport


def test_readiness_report_serializes_as_plain_backend_diagnostic_data():
    report = ArchitecturalReadinessReport(
        ready_for_lego=True,
        blockers=[],
        spatial=SpatialRelationReport(scene_id="generic", envelopes=[], pairs=[]),
    )
    assert report.model_dump()["ready_for_lego"] is True
