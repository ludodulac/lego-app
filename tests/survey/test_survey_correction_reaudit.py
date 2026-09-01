from __future__ import annotations

import json
from pathlib import Path

from brickhouse.survey import ArchitecturalSurvey, SurveyCorrection, SurveyRelation
from brickhouse.survey.correction_reaudit import build_survey_correction_reaudit_scope


FIXTURE = Path(__file__).parents[1] / "fixtures" / "architectural_survey_real_house_photos_1_2.json"


def _survey() -> ArchitecturalSurvey:
    survey = ArchitecturalSurvey.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    survey.relations.append(
        SurveyRelation.model_validate(
            {
                "id": "window-to-front-boundary",
                "kind": "part_of",
                "subject_id": "front_upper_left_window",
                "object_id": "front_boundary",
                "certainty": "certain",
                "statement": "The upper-left opening belongs to the front facade boundary.",
                "evidence": [
                    {"photo_index": 1, "observation": "Opening and facade are visible together."}
                ],
            }
        )
    )
    return survey


def test_reaudit_scope_includes_changed_observation_incident_relations_and_photos() -> None:
    original = _survey()
    candidate = original.model_copy(deep=True)
    target = next(item for item in candidate.observations if item.id == "front_upper_left_window")
    target.attributes["facade_horizontal_rank"] = 3
    correction = SurveyCorrection.model_validate(
        {
            "survey_id": original.id,
            "candidate": candidate,
            "changes": [
                {
                    "id": "change-reorient-window",
                    "finding_id": "audit-reorient-window",
                    "object_type": "observation",
                    "source_id": "front_upper_left_window",
                    "candidate_id": "front_upper_left_window",
                    "action": "reorient",
                    "message": "Reorient the audited opening.",
                }
            ],
        }
    )

    scope = build_survey_correction_reaudit_scope(original, correction)

    assert scope.correction_change_ids == ["change-reorient-window"]
    assert scope.observation_ids == ["front_upper_left_window"]
    assert scope.relation_ids == ["window-to-front-boundary"]
    assert scope.photo_indexes == [1]


def test_reaudit_scope_reads_removed_relation_evidence_from_original() -> None:
    original = _survey()
    candidate = original.model_copy(deep=True)
    candidate.relations = [
        item for item in candidate.relations if item.id != "window-to-front-boundary"
    ]
    correction = SurveyCorrection.model_validate(
        {
            "survey_id": original.id,
            "candidate": candidate,
            "changes": [
                {
                    "id": "change-remove-relation",
                    "finding_id": "audit-remove-relation",
                    "object_type": "relation",
                    "source_id": "window-to-front-boundary",
                    "candidate_id": None,
                    "action": "remove",
                    "message": "Remove the unsupported relation.",
                }
            ],
        }
    )

    scope = build_survey_correction_reaudit_scope(original, correction)

    assert scope.observation_ids == []
    assert scope.relation_ids == ["window-to-front-boundary"]
    assert scope.photo_indexes == [1]
