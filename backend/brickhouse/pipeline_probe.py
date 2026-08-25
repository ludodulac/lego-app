"""Deterministic diagnostic runner for Survey -> Scene -> BuildingModel -> M0.

This module is intentionally generic: it accepts any validated Survey/Scene JSON pair
and reports the first layer that blocks. It never patches input data or invents missing
geometry. CI and engineering investigations can use the same runner as the web flow.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene, validate_scene_against_survey
from brickhouse.scene.topology_projection import project_scene_to_building
from brickhouse.survey import ArchitecturalSurvey


def probe_pipeline(survey: ArchitecturalSurvey, scene: ArchitecturalScene) -> dict:
    survey_issues = validate_scene_against_survey(survey, scene)
    survey_errors = [issue for issue in survey_issues if issue.severity.value == "error"]
    report = {
        "scene_schema_valid": True,
        "survey_issue_codes": [issue.code for issue in survey_issues],
        "first_blocking_stage": None,
        "projection_issue_codes": [],
        "m0_error": None,
    }
    if survey_errors:
        report["first_blocking_stage"] = "survey_fidelity"
        return report

    projection = project_scene_to_building(scene)
    report["projection_issue_codes"] = [issue.code for issue in projection.issues]
    if projection.blocked or projection.building is None:
        report["first_blocking_stage"] = "scene_to_building_projection"
        return report

    try:
        run_m0_pipeline_scene(scene)
    except Exception as exc:  # diagnostic boundary: preserve the exact downstream failure
        report["first_blocking_stage"] = "m0_pipeline"
        report["m0_error"] = f"{type(exc).__name__}: {exc}"
        return report

    report["first_blocking_stage"] = "none"
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("survey", type=Path)
    parser.add_argument("scene", type=Path)
    args = parser.parse_args()
    survey = ArchitecturalSurvey.model_validate_json(args.survey.read_text(encoding="utf-8"))
    scene = ArchitecturalScene.model_validate_json(args.scene.read_text(encoding="utf-8"))
    print(json.dumps(probe_pipeline(survey, scene), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
