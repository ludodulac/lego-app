from brickhouse.scene.readiness import ArchitecturalReadinessReport
from brickhouse.scene.spatial_analysis import SpatialRelationReport


def test_zero_blockers_means_ready():
    report = ArchitecturalReadinessReport(
        ready_for_lego=True,
        blockers=[],
        spatial=SpatialRelationReport(scene_id="scene", envelopes=[], pairs=[]),
    )
    assert report.ready_for_lego
