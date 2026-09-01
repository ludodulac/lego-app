from fastapi.testclient import TestClient

from brickhouse.api import app


client = TestClient(app)


def _survey(*, invalid_opening: bool = False) -> dict:
    observations = []
    if invalid_opening:
        observations.append(
            {
                "id": "opening-1",
                "kind": "opening",
                "facade": "front",
                "certainty": "certain",
                "statement": "Une ouverture est visible.",
                "evidence": [
                    {"photo_index": 1, "observation": "Ouverture visible."}
                ],
                "attributes": {},
                "attribute_certainty": {},
            }
        )
    return {
        "schema_version": "0.1",
        "id": "survey-api-test",
        "name": "Survey API test",
        "canonical_frame": {
            "front_facade": "front",
            "x_direction": "front_view_left_to_right",
            "y_direction": "front_to_rear",
            "z_direction": "bottom_to_top",
        },
        "photos": [
            {
                "photo_index": 1,
                "capture_role": "facade_view",
                "facade": "front",
                "description": "Vue de test.",
                "source": {"kind": "observed", "confidence": 1.0},
                "image_left_maps_to_facade_offset": "low",
                "user_note": None,
            }
        ],
        "known_measurements": [],
        "observations": observations,
        "relations": [],
        "representation_policy": {
            "preserve_nominal_materials": True,
            "preserve_opening_composition": True,
            "preserve_architectural_details": True,
            "reproduce_weathering": False,
            "reproduce_temporary_objects": False,
        },
        "notes": None,
    }


def _audit(*, photo_index: int = 1) -> dict:
    return {
        "schema_version": "0.1",
        "kind": "survey_audit",
        "survey_id": "survey-api-test",
        "summary": {"status": "needs_correction", "issue_count": 1},
        "findings": [
            {
                "id": "audit-missing-roof",
                "status": "missing",
                "target_type": "survey",
                "target_id": None,
                "severity": "warning",
                "photo_evidence": [
                    {
                        "photo_index": photo_index,
                        "observation": "Une toiture est visible.",
                    }
                ],
                "message": "La toiture visible manque au Survey.",
                "suggested_action": "add",
            }
        ],
    }


def test_validate_survey_audit_accepts_valid_diagnostic_without_mutation() -> None:
    survey = _survey()
    audit = _audit()

    response = client.post(
        "/api/v1/validate-survey-audit",
        json={"survey": survey, "audit": audit},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["needs_correction"] is True
    assert body["issues"] == []
    assert body["audit"] == audit
    assert survey == _survey()


def test_validate_survey_audit_rejects_unknown_photo_reference() -> None:
    response = client.post(
        "/api/v1/validate-survey-audit",
        json={"survey": _survey(), "audit": _audit(photo_index=2)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["needs_correction"] is False
    assert [issue["code"] for issue in body["issues"]] == [
        "survey_audit_unknown_photo"
    ]


def test_validate_survey_audit_requires_backend_valid_survey_first() -> None:
    pass_audit = {
        "schema_version": "0.1",
        "kind": "survey_audit",
        "survey_id": "survey-api-test",
        "summary": {"status": "pass", "issue_count": 0},
        "findings": [],
    }

    response = client.post(
        "/api/v1/validate-survey-audit",
        json={"survey": _survey(invalid_opening=True), "audit": pass_audit},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    assert body["needs_correction"] is False
    assert "survey_opening_not_single_physical_object" in {
        issue["code"] for issue in body["issues"]
    }
