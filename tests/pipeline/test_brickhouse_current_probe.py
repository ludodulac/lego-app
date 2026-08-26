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


def test_current_brickhouse_preserves_bounded_shed_without_inventing_pitch() -> None:
    scene = _scene()
    roof = next(item for item in scene.roofs if item.id == "roof_main")
    assert roof.type.value == "shed"
    assert roof.down_slope_direction.value == "rear"
    assert roof.pitch_degrees is None
    assert roof.pitch_range_degrees is not None
    assert roof.pitch_range_degrees.min_degrees == 10
    assert roof.pitch_range_degrees.max_degrees == 35


def test_current_brickhouse_probe_reaches_expected_exact_pitch_blocker() -> None:
    survey = _survey()
    scene = _scene()
    fidelity_issues = validate_scene_against_survey(survey, scene)
    assert [issue.code for issue in fidelity_issues if issue.severity.value == "error"] == []

    projection = project_scene_to_building(scene)
    blockers = [issue for issue in projection.issues if issue.severity.value == "blocker"]
    assert [issue.code for issue in blockers] == ["shed_geometry_incomplete"]
    assert blockers[0].object_id == "roof_main"
    assert "10–35°" in blockers[0].message
    assert "midpoint" in blockers[0].message
    assert "endpoint" in blockers[0].message
    assert "default" in blockers[0].message

    report = probe_pipeline(survey, scene)
    assert report["first_blocking_stage"] == "scene_to_building_projection"
    assert "shed_geometry_incomplete" in report["projection_issue_codes"]
    assert report["m0_error"] is None
