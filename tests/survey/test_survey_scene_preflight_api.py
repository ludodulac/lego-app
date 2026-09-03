from fastapi.testclient import TestClient

from brickhouse.api import app


client = TestClient(app)


def _semantically_invalid_survey() -> dict:
    return {
        "schema_version": "0.1",
        "id": "survey-preflight",
        "name": "Survey preflight",
        "photos": [
            {
                "photo_index": 1,
                "facade": "front",
                "description": "front",
                "source": {"kind": "user_provided", "confidence": 0.99},
                "image_left_maps_to_facade_offset": "low",
            }
        ],
        "known_measurements": [
            {
                "kind": "front_width",
                "value": 10.0,
                "units": "m",
                "source": {"kind": "user_provided", "confidence": 0.99},
            }
        ],
        "observations": [
            {
                "id": "grouped_front_openings",
                "kind": "opening",
                "facade": "front",
                "certainty": "certain",
                "statement": "Three front windows",
                "evidence": [{"photo_index": 1, "observation": "visible"}],
                "attributes": {
                    "physical_object_count": 3,
                    "semantic_type": "window",
                },
            }
        ],
    }


def _scene() -> dict:
    return {
        "schema_version": "0.2",
        "id": "scene-preflight",
        "name": "Scene preflight",
        "units": "m",
        "volumes": [
            {
                "id": "main",
                "position": {"x": 0, "y": 0, "z": 0},
                "width": {
                    "value": 10,
                    "source": {"kind": "user_provided", "confidence": 1},
                },
                "depth": {
                    "value": 8,
                    "source": {"kind": "inferred", "confidence": 0.7},
                },
                "height": {
                    "value": 6,
                    "source": {"kind": "inferred", "confidence": 0.7},
                },
                "floors": 2,
                "source": {"kind": "inferred", "confidence": 0.7},
            }
        ],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "dark_brown"},
        },
    }


def test_scene_fusion_rejects_survey_that_skipped_semantic_validation() -> None:
    response = client.post(
        "/api/v1/validate-scene-against-survey",
        json={"survey": _semantically_invalid_survey(), "scene": _scene()},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["valid_for_projection"] is False
    assert payload["projection"] is None
    assert "survey_opening_not_single_physical_object" in {
        issue["code"] for issue in payload["issues"]
    }


def test_validate_survey_rejects_truncated_json_clearly() -> None:
    response = client.post(
        "/api/v1/validate-survey",
        content='{"schema_version":"0.1","id":"truncated"',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert any(issue.get("type") == "json_invalid" for issue in detail)
