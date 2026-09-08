from __future__ import annotations

import json
from pathlib import Path

from brickhouse.survey import ArchitecturalSurvey, SurveyAudit, SurveyCorrection, validate_survey_correction
from brickhouse.survey.correction_reaudit import build_survey_correction_reaudit_scope


FIXTURE = Path(__file__).parents[1] / "fixtures" / "brickhouse_survey_current.json"


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _orientation_audit(survey: ArchitecturalSurvey) -> SurveyAudit:
    return SurveyAudit.model_validate(
        {
            "schema_version": "0.1",
            "kind": "survey_audit",
            "survey_id": survey.id,
            "summary": {"status": "needs_correction", "issue_count": 2},
            "findings": [
                {
                    "id": "real-house-5-photo-3-rear",
                    "status": "disputed",
                    "target_type": "photo",
                    "target_id": "3",
                    "severity": "warning",
                    "photo_evidence": [
                        {
                            "photo_index": 3,
                            "observation": (
                                "Human-confirmed rear view; only part of the rear is visible and "
                                "the remainder is occluded by the neighboring building."
                            ),
                        }
                    ],
                    "message": "Photo 3 is rear, not left; occluded rear content remains unknown.",
                    "suggested_action": "reorient",
                },
                {
                    "id": "real-house-5-photo-5-left",
                    "status": "disputed",
                    "target_type": "photo",
                    "target_id": "5",
                    "severity": "warning",
                    "photo_evidence": [
                        {
                            "photo_index": 5,
                            "observation": "Human-confirmed left-side view of the target building.",
                        }
                    ],
                    "message": "Photo 5 is left, not rear.",
                    "suggested_action": "reorient",
                },
            ],
        }
    )


def _orientation_correction(
    survey: ArchitecturalSurvey,
    audit: SurveyAudit,
) -> SurveyCorrection:
    candidate = survey.model_copy(deep=True)
    candidate.photos[2] = candidate.photos[2].model_copy(update={"facade": "rear"})
    candidate.photos[4] = candidate.photos[4].model_copy(update={"facade": "left"})

    return SurveyCorrection.model_validate(
        {
            "schema_version": "0.1",
            "kind": "survey_correction",
            "survey_id": survey.id,
            "candidate": candidate,
            "changes": [
                {
                    "id": "change-real-house-5-photo-3-rear",
                    "finding_id": "real-house-5-photo-3-rear",
                    "object_type": "photo",
                    "source_id": "3",
                    "candidate_id": "3",
                    "action": "reorient",
                    "message": "Apply only the human-confirmed facade orientation for photo 3.",
                },
                {
                    "id": "change-real-house-5-photo-5-left",
                    "finding_id": "real-house-5-photo-5-left",
                    "object_type": "photo",
                    "source_id": "5",
                    "candidate_id": "5",
                    "action": "reorient",
                    "message": "Apply only the human-confirmed facade orientation for photo 5.",
                },
            ],
        }
    )


def test_real_house_5_human_orientation_correction_is_bounded_and_audit_linked() -> None:
    source = _survey()
    source_snapshot = source.model_copy(deep=True)
    audit = _orientation_audit(source)
    correction = _orientation_correction(source, audit)

    assert validate_survey_correction(source, audit, correction) == []
    assert source == source_snapshot

    assert [photo.facade for photo in source.photos] == ["front", "right", "left", "left", "rear"]
    assert [photo.facade for photo in correction.candidate.photos] == [
        "front",
        "right",
        "rear",
        "left",
        "left",
    ]

    # BH-185 deliberately freezes measurements and non-orientation photo content.
    # This correction must neither create nor reinterpret metric truth.
    assert correction.candidate.known_measurements == source.known_measurements
    assert correction.candidate.photos[2].description == source.photos[2].description
    assert correction.candidate.photos[4].description == source.photos[4].description


def test_real_house_5_orientation_reaudit_is_limited_to_confirmed_views() -> None:
    source = _survey()
    audit = _orientation_audit(source)
    correction = _orientation_correction(source, audit)

    scope = build_survey_correction_reaudit_scope(source, correction)

    assert scope.correction_change_ids == [
        "change-real-house-5-photo-3-rear",
        "change-real-house-5-photo-5-left",
    ]
    assert scope.photo_indexes == [3, 5]
    assert scope.observation_ids == []
    assert scope.relation_ids == []
