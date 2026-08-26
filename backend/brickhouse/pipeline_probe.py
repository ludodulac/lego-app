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


def _required_inputs_for_projection(scene: ArchitecturalScene, projection) -> list[dict]:
    """Describe missing inputs without guessing values or changing projection semantics."""
    required: list[dict] = []
    roofs = {roof.id: roof for roof in scene.roofs}
    volumes = {volume.id: volume for volume in scene.volumes}

    for issue in projection.issues:
        if issue.severity.value != "blocker" or issue.object_id is None:
            continue

        if issue.code == "shed_geometry_incomplete":
            roof = roofs.get(issue.object_id)
            if roof is None:
                continue
            if roof.down_slope_direction is None:
                required.append({
                    "object_id": roof.id,
                    "field": "down_slope_direction",
                    "kind": "categorical_geometry",
                    "reason": "shed_construction_requires_fall_direction",
                })
            if roof.pitch_degrees is None:
                item = {
                    "object_id": roof.id,
                    "field": "pitch_degrees",
                    "kind": "exact_metric",
                    "reason": "shed_construction_requires_exact_pitch",
                }
                if roof.pitch_range_degrees is not None:
                    item["known_range_degrees"] = {
                        "min": roof.pitch_range_degrees.min_degrees,
                        "max": roof.pitch_range_degrees.max_degrees,
                    }
                required.append(item)

        elif issue.code == "gable_geometry_incomplete":
            roof = roofs.get(issue.object_id)
            if roof is None:
                continue
            if roof.ridge_direction is None:
                required.append({
                    "object_id": roof.id,
                    "field": "ridge_direction",
                    "kind": "categorical_geometry",
                    "reason": "gable_construction_requires_ridge_direction",
                })
            if roof.pitch_degrees is None:
                item = {
                    "object_id": roof.id,
                    "field": "pitch_degrees",
                    "kind": "exact_metric",
                    "reason": "gable_construction_requires_exact_pitch",
                }
                if roof.pitch_range_degrees is not None:
                    item["known_range_degrees"] = {
                        "min": roof.pitch_range_degrees.min_degrees,
                        "max": roof.pitch_range_degrees.max_degrees,
                    }
                required.append(item)

        elif issue.code == "volume_geometry_incomplete":
            volume = volumes.get(issue.object_id)
            if volume is None:
                continue
            for field in ("width", "depth", "height"):
                if getattr(volume, field).value is None:
                    required.append({
                        "object_id": volume.id,
                        "field": field,
                        "kind": "exact_metric",
                        "reason": "building_projection_requires_metric_envelope",
                    })

    return required


def probe_pipeline(survey: ArchitecturalSurvey, scene: ArchitecturalScene) -> dict:
    survey_issues = validate_scene_against_survey(survey, scene)
    survey_errors = [issue for issue in survey_issues if issue.severity.value == "error"]
    report = {
        "scene_schema_valid": True,
        "survey_issue_codes": [issue.code for issue in survey_issues],
        "first_blocking_stage": None,
        "projection_issue_codes": [],
        "required_inputs": [],
        "m0_error": None,
    }
    if survey_errors:
        report["first_blocking_stage"] = "survey_fidelity"
        return report

    projection = project_scene_to_building(scene)
    report["projection_issue_codes"] = [issue.code for issue in projection.issues]
    report["required_inputs"] = _required_inputs_for_projection(scene, projection)
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
