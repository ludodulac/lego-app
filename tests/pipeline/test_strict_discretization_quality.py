from pathlib import Path

from brickhouse.building.validation import load_building_model
from brickhouse.pipeline import run_m0_pipeline_model


FIXTURE = Path("docs/examples/building-model-simple-house.json")


def test_strict_building_export_contains_grid_rounding_quality():
    building = load_building_model(FIXTURE)
    bundle = run_m0_pipeline_model(building, front_width_studs=48)

    reports = bundle.metadata.discretization_quality
    assert reports
    assert reports[0].volume_id == building.volumes[0].id
    assert len(reports[0].walls) == 4
    assert reports[0].worst_absolute_error_m >= reports[0].mean_absolute_error_m >= 0

    quantities = {
        error.quantity
        for report in reports
        for wall in report.walls
        for error in wall.errors
    }
    assert "wall_width" in quantities
    assert "wall_height" in quantities


def test_strict_export_quality_is_deterministic():
    building = load_building_model(FIXTURE)
    first = run_m0_pipeline_model(building, front_width_studs=48)
    second = run_m0_pipeline_model(building, front_width_studs=48)
    assert first.metadata.discretization_quality == second.metadata.discretization_quality
