from copy import deepcopy

from brickhouse.survey import (
    ArchitecturalSurvey,
    analyze_multiview_identity,
    validate_survey_semantics,
)

SOURCE = {"kind": "inferred", "confidence": 0.7}


def _survey(*, identity=None, certainty="certain", evidence=(1, 2)):
    attributes = {}
    attribute_certainty = {}
    if identity is not None:
        attributes["multiview_identity"] = identity
        attribute_certainty["multiview_identity"] = certainty
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "multiview-test",
        "name": "Multiview test",
        "photos": [
            {"photo_index": 1, "facade": "front", "description": "front", "source": SOURCE, "image_left_maps_to_facade_offset": "low"},
            {"photo_index": 2, "facade": "right", "description": "right", "source": SOURCE, "image_left_maps_to_facade_offset": "low"},
            {"photo_index": 3, "facade": "rear", "description": "rear", "source": SOURCE, "image_left_maps_to_facade_offset": "low"},
        ],
        "observations": [{
            "id": "chimney-a",
            "kind": "chimney",
            "certainty": "certain",
            "statement": "chimney candidate tracked across views",
            "evidence": [{"photo_index": index, "observation": f"candidate visible in photo {index}"} for index in evidence],
            "attributes": attributes,
            "attribute_certainty": attribute_certainty,
        }],
    })


def _codes(survey):
    return {issue.code for issue in validate_survey_semantics(survey)}


def test_certain_same_object_identity_accepts_discriminating_cue():
    survey = _survey(identity={
        "status": "same_physical_object",
        "photo_indexes": [1, 2],
        "cues": ["relative_position", "shape_detail"],
    })

    report = analyze_multiview_identity(survey)

    assert report.issues == []
    assert report.facts[0].identity.photo_indexes == [1, 2]


def test_certain_same_object_identity_requires_discriminating_cue():
    survey = _survey(identity={
        "status": "same_physical_object",
        "photo_indexes": [1, 2],
        "cues": [],
    })

    assert "certain_multiview_identity_missing_discriminating_cue" in _codes(survey)


def test_unresolved_identity_cannot_be_certain():
    survey = _survey(identity={
        "status": "unresolved",
        "photo_indexes": [1, 2],
        "cues": [],
    })

    assert "unresolved_multiview_identity_cannot_be_certain" in _codes(survey)


def test_identity_photo_indexes_must_be_backed_by_observation_evidence():
    survey = _survey(
        identity={"status": "same_physical_object", "photo_indexes": [1, 3], "cues": ["shape_detail"]},
        evidence=(1, 2),
    )

    assert "multiview_identity_missing_evidence_photo" in _codes(survey)


def test_legacy_multiphoto_observation_remains_valid_without_new_attribute():
    survey = _survey(identity=None)
    before = deepcopy(survey.model_dump())

    report = analyze_multiview_identity(survey)

    assert report.facts == []
    assert report.issues == []
    assert survey.model_dump() == before


def test_unresolved_identity_preserves_uncertainty_without_invention():
    survey = _survey(
        identity={"status": "unresolved", "photo_indexes": [1, 2], "cues": []},
        certainty="unproven",
    )
    before = deepcopy(survey.model_dump())

    report = analyze_multiview_identity(survey)

    assert report.issues == []
    assert report.facts[0].certainty.value == "unproven"
    assert survey.model_dump() == before
