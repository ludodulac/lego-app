from __future__ import annotations

import json
from pathlib import Path

from brickhouse.survey import ArchitecturalSurvey


FIXTURE = (
    Path(__file__).parents[2]
    / "frontend"
    / "benchmarks"
    / "real-house-5"
    / "accepted-survey-v0.1.json"
)


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))


def test_real_house_5_accepted_orientation_matches_human_confirmed_walkaround() -> None:
    """Guard the accepted capture order; do not invent a corrective reorientation.

    Human confirmation on 2026-09-08 established that the existing accepted
    capture hints are correct: front, right, two complementary left views, then
    the partially observable rear.  Photo 3 approaches the rear through the
    terrace but is still a left-side capture; photo 5 is the rear capture.
    """
    survey = _survey()

    assert survey.known_measurements == []
    assert [photo.facade for photo in survey.photos] == [
        "front",
        "right",
        "left",
        "left",
        "rear",
    ]


def test_real_house_5_orientation_truth_does_not_promote_hidden_rear_content() -> None:
    survey = _survey()

    # The rear capture is evidence only for objects it actually observes.  The
    # orientation itself must never be used as permission to synthesize rear
    # openings or measurements.
    rear_photo = survey.photos[4]
    assert rear_photo.photo_index == 5
    assert rear_photo.facade == "rear"
    assert survey.known_measurements == []

    rear_openings = [
        item
        for item in survey.observations
        if item.kind == "opening" and item.facade == "rear"
    ]
    assert rear_openings == []

    photo_5_evidence_ids = {
        item.id
        for item in survey.observations
        if any(evidence.photo_index == 5 for evidence in item.evidence)
    }
    assert "stair-exterior-1" in photo_5_evidence_ids
    assert "platform-massive-1" in photo_5_evidence_ids
    assert "volume-exterior-1" in photo_5_evidence_ids
