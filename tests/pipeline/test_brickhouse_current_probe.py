import json
from pathlib import Path

from brickhouse.pipeline_probe import probe_pipeline
from brickhouse.scene import ArchitecturalScene, project_scene_to_building, validate_scene_against_survey
from brickhouse.survey import ArchitecturalSurvey


FIXTURES = Path(__file__).parents[1] / "fixtures"
SURVEY = FIXTURES / "brickhouse_survey_current.json"
SCENE = FIXTURES / "brickhouse_scene_current.json"


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(json.loads(SURVEY.read_text(encoding="utf-8")))


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate(json.loads(SCENE.read_text(encoding="utf-8")))


def expected_roof_inputs() -> list[dict]:
    return [
        {"object_id": "roof_main", "field": "down_slope_direction", "kind": "categorical_geometry", "reason": "shed_construction_requires_fall_direction"},
        {"object_id": "roof_main", "field": "pitch_degrees", "kind": "exact_metric", "reason": "shed_construction_requires_exact_pitch"},
    ]


def test_current_brickhouse_preserves_unresolved_shed_without_inventing_geometry() -> None:
    roof = next(item for item in _scene().roofs if item.id == "roof_main")
    assert roof.type.value == "shed"
    assert roof.down_slope_direction is None
    assert roof.pitch_degrees is None
    assert roof.pitch_range_degrees is None


def test_current_brickhouse_probe_stops_at_lost_terrace_structure_before_projection() -> None:
    survey = _survey()
    scene = _scene()
    fidelity_issues = validate_scene_against_survey(survey, scene)
    error_codes = [issue.code for issue in fidelity_issues if issue.severity.value == "error"]
    assert error_codes == ["certain_platform_support_structure_lost"]

    # Projection still exposes its own blockers when called directly, but the public
    # pipeline probe must stop earlier: known architectural truth cannot be discarded
    # merely because downstream geometry could otherwise be projected.
    projection = project_scene_to_building(scene)
    blockers = [issue for issue in projection.issues if issue.severity.value == "blocker"]
    assert [issue.code for issue in blockers].count("shed_geometry_incomplete") == 1
    assert [issue.code for issue in blockers].count("topological_relation_geometry_unresolved") == 2
    roof_blocker = next(issue for issue in blockers if issue.code == "shed_geometry_incomplete")
    assert roof_blocker.object_id == "roof_main"
    assert "down_slope_direction" in roof_blocker.message
    assert "pitch_degrees" in roof_blocker.message
    assert "rather than inventing" in roof_blocker.message
    assert "10–35°" not in roof_blocker.message

    report = probe_pipeline(survey, scene)
    assert report["first_blocking_stage"] == "survey_fidelity"
    assert "certain_platform_support_structure_lost" in report["survey_issue_codes"]
    assert report["projection_issue_codes"] == []
    assert report["required_inputs"] == []
    assert report["m0_error"] is None
