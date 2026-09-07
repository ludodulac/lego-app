from copy import deepcopy

from brickhouse.survey import (
    ArchitecturalSurvey,
    SubjectOwnership,
    analyze_subject_ownership,
    validate_survey_semantics,
)


SOURCE = {"kind": "inferred", "confidence": 0.7}


def _observation(
    observation_id: str,
    *,
    kind: str = "chimney",
    ownership: str | None = None,
    ownership_certainty: str = "certain",
    photo_indexes=(1,),
):
    attributes = {}
    attribute_certainty = {}
    if ownership is not None:
        attributes["subject_ownership"] = ownership
        attribute_certainty["subject_ownership"] = ownership_certainty
    return {
        "id": observation_id,
        "kind": kind,
        "facade": "front" if kind not in {"context", "occlusion"} else None,
        "certainty": "certain",
        "statement": f"visible object {observation_id}",
        "evidence": [
            {"photo_index": index, "observation": f"{observation_id} visible in photo {index}"}
            for index in photo_indexes
        ],
        "attributes": attributes,
        "attribute_certainty": attribute_certainty,
    }


def _survey(observations, relations=None):
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "ownership-survey",
        "name": "Ownership survey",
        "photos": [
            {
                "photo_index": 1,
                "facade": "front",
                "description": "front view containing target and neighboring context",
                "source": SOURCE,
                "image_left_maps_to_facade_offset": "low",
            },
            {
                "photo_index": 2,
                "facade": "right",
                "description": "second view used for identity tracking",
                "source": SOURCE,
                "image_left_maps_to_facade_offset": "low",
            },
        ],
        "observations": observations,
        "relations": relations or [],
    })


def _codes(survey):
    return {issue.code for issue in validate_survey_semantics(survey)}


def test_target_and_external_context_are_machine_readable_without_metric_inference():
    survey = _survey([
        _observation("target-chimney", ownership="target_building", photo_indexes=(1, 2)),
        _observation("neighbor-chimney", ownership="external_context", photo_indexes=(1, 2)),
    ])

    report = analyze_subject_ownership(survey)

    assert report.issues == []
    assert [fact.ownership for fact in report.facts] == [
        SubjectOwnership.EXTERNAL_CONTEXT,
        SubjectOwnership.TARGET_BUILDING,
    ]
    assert report.facts[0].evidence_photo_indexes == [1, 2]


def test_unresolved_ownership_cannot_be_promoted_to_certain():
    survey = _survey([
        _observation("ambiguous-roof", kind="roof", ownership="unresolved", ownership_certainty="certain"),
    ])

    assert "unresolved_ownership_cannot_be_certain" in _codes(survey)


def test_context_observation_cannot_claim_target_building_ownership():
    survey = _survey([
        _observation("neighbor-context", kind="context", ownership="target_building"),
    ])

    assert "context_observation_cannot_be_target_owned" in _codes(survey)


def test_certain_same_physical_object_relation_cannot_bridge_target_and_context():
    survey = _survey(
        [
            _observation("target-chimney", ownership="target_building"),
            _observation("neighbor-chimney", ownership="external_context", photo_indexes=(2,)),
        ],
        relations=[{
            "id": "bad-identity",
            "kind": "same_physical_object",
            "subject_id": "target-chimney",
            "object_id": "neighbor-chimney",
            "certainty": "certain",
            "statement": "incorrectly merged from visual similarity",
            "evidence": [
                {"photo_index": 1, "observation": "first chimney visible"},
                {"photo_index": 2, "observation": "second chimney visible"},
            ],
        }],
    )

    assert "contradictory_ownership_identity_relation" in _codes(survey)


def test_adjacency_does_not_force_same_ownership():
    survey = _survey(
        [
            _observation("target-volume", kind="volume", ownership="target_building"),
            _observation("neighbor-volume", kind="volume", ownership="external_context", photo_indexes=(2,)),
        ],
        relations=[{
            "id": "adjacent-buildings",
            "kind": "adjacent_to",
            "subject_id": "target-volume",
            "object_id": "neighbor-volume",
            "certainty": "certain",
            "statement": "buildings are adjacent but distinct",
            "evidence": [{"photo_index": 1, "observation": "separate wall boundaries visible"}],
        }],
    )

    assert "contradictory_ownership_identity_relation" not in _codes(survey)


def test_legacy_survey_without_ownership_remains_valid_and_analysis_is_non_mutating():
    survey = _survey([_observation("legacy-opening", kind="opening")])
    before = deepcopy(survey.model_dump())

    report = analyze_subject_ownership(survey)

    assert report.facts == []
    assert report.issues == []
    assert survey.model_dump() == before
