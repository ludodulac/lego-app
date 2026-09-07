from brickhouse.scene.readiness import ArchitecturalReadinessReport
from brickhouse.scene.spatial_analysis import SpatialRelationReport


def test_readiness_report_is_separate_from_scene_contract():
    report = ArchitecturalReadinessReport(
        ready_for_lego=False,
        blockers=[],
        spatial=SpatialRelationReport(scene_id="scene", envelopes=[], pairs=[]),
    )
    assert "scene" not in report.model_fields
