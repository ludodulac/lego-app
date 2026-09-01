from fastapi.testclient import TestClient

from brickhouse.api import app


client = TestClient(app)


def _survey() -> dict:
    return {
        "schema_version": "0.1",
        "id": "survey-correction-api-test",
        "name": "Survey correction API test",
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
                "description": "Vue avant de test.",
                "source": {"kind": "observed", "confidence": 1.0},
                "image_left_maps_to_facade_offset": "low",
                "user_note": None,
            }
        ],
        "known_measurements": [
            {
                "kind": "front_width",
                "value": 10.0,
                "units": "m",
                "source": {"kind": "user_provided", "confidence": 1.0},
            }
        ],
        "observations": [],
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
        "survey_id": "survey-correction-api-test",
        "summary": {"status": "needs_correction", "issue_count": 1},
        "findings": [
            {
                "id": "audit-missing-roof",
                "status": "missing",
                "target_type": "survey",
                "target_id": None,
                "severity": "error",
                "photo_evidence": [
                    {"photo_index": photo_index, "observation": "Toiture visible."}
                ],
                "message": "Une toiture visible manque au Survey.",
                "suggested_action": "add",
            }
        ],
    }


def _roof_observation(item_id: str = "audit-added-roof") -> dict:
    return {
        "id": item_id,
        "kind": "roof",
        "facade": "front",
        "certainty": "certain",
        "statement": "Une rive de toiture est visible au-dessus de la façade avant.",
        "evidence": [{"photo_index": 1, "observation": "Rive visible."}],
        "attributes": {"roof_edge_type": "rake_or_gable_edge"},
        "attribute_certainty": {"roof_edge_type": "plausible"},
    }


def _correction(*, with_extra: bool = False) -> dict:
    candidate = _survey()
    candidate["observations"].append(_roof_observation())
    if with_extra:
        candidate["observations"].append(
            {
                "id": "undeclared-chimney",
                "kind": "chimney",
                "facade": "front",
                "certainty": "plausible",
                "statement": "Un élément vertical est visible.",
                "evidence": [
                    {"photo_index": 1, "observation": "Élément vertical visible."}
                ],
                "attributes": {},
                "attribute_certainty": {},
            }
        )
    return {
        "schema_version": "0.1",
        "kind": "survey_correction",
        "survey_id": "survey-correction-api-test",
        "candidate": candidate,
        "changes": [
            {
                "id": "change-add-roof",
                "finding_id": "audit-missing-roof",
                "object_type": "observation",
                "source_id": None,
                "candidate_id": "audit-added-roof",
                "action": "add",
                "message": "Ajoute uniquement la toiture signalée par l'audit.",
            }
        ],
    }


def test_validate_survey_correction_accepts_explicit_candidate() -> None:
    payload = {
        "original": _survey(),
        "audit": _audit(),
        "correction": _correction(),
    }

    response = client.post("/api/v1/validate-survey-correction", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["valid_for_reaudit"] is True
    assert body["issues"] == []
    assert body["correction"]["survey_id"] == "survey-correction-api-test"
    assert body["correction"]["changes"][0]["finding_id"] == "audit-missing-roof"
    assert payload["original"]["known_measurements"][0]["value"] == 10.0


def test_validate_survey_correction_rejects_invalid_source_audit_first() -> None:
    response = client.post(
        "/api/v1/validate-survey-correction",
        json={
            "original": _survey(),
            "audit": _audit(photo_index=2),
            "correction": _correction(),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid_for_reaudit"] is False
    assert [issue["code"] for issue in body["issues"]] == [
        "survey_audit_unknown_photo"
    ]


def test_validate_survey_correction_rejects_undeclared_mutation() -> None:
    response = client.post(
        "/api/v1/validate-survey-correction",
        json={
            "original": _survey(),
            "audit": _audit(),
            "correction": _correction(with_extra=True),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["valid_for_reaudit"] is False
    assert "survey_correction_undeclared_addition" in {
        issue["code"] for issue in body["issues"]
    }
