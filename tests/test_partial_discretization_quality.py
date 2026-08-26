import json
from pathlib import Path

from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.scene.models import ArchitecturalScene


FIXTURE = Path("tests/fixtures/brickhouse_scene_current.json")


def _current_scene() -> ArchitecturalScene:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    # This legacy reference fixture intentionally stores the unmeasured grade as null.
    # Terrain is omitted from the conservative core-shell build, so neutralizing those
    # two legacy fields here only lets the current schema validate the same photo scene.
    for profile in (data.get("terrain") or {}).get("profiles", []):
        if profile.get("start_elevation") is None:
            profile["start_elevation"] = 0.0
        if profile.get("end_elevation") is None:
            profile["end_elevation"] = 0.0
    return ArchitecturalScene.model_validate(data)


def test_current_five_photo_partial_build_exports_grid_rounding_quality():
    scene = _current_scene()
    bundle = run_partial_scene_pipeline(scene, front_width_studs=48)

    reports = bundle.metadata.discretization_quality
    assert reports
    assert reports[0].volume_id == "volume_main"
    assert reports[0].walls
    assert reports[0].worst_absolute_error_m >= reports[0].mean_absolute_error_m >= 0

    opening_errors = [
        error
        for report in reports
        for wall in report.walls
        for error in wall.errors
        if error.quantity.startswith("opening_")
    ]
    assert opening_errors
    assert {error.quantity for error in opening_errors} >= {
        "opening_x", "opening_width", "opening_sill", "opening_height"
    }

    # Grid rounding is separate from uncertainty in the photo-derived architecture.
    codes = {issue.code for issue in bundle.fidelity_issues}
    assert "low_confidence_partial_dimension" in codes
    assert "low_confidence_partial_opening_geometry" in codes
