from copy import deepcopy

from fastapi.testclient import TestClient

from brickhouse.api import app


client = TestClient(app)


def _survey_payload() -> dict:
    return {
        "schema_version": "0.1",
        "id": "generic-http-house",
        "name": "Generic HTTP house",
        "photos": [
            {
                "photo_index": 1,
                "facade": "front",
                "description": "Canonical front view.",
                "source": {"kind": "observed", "confidence": 1.0},
                "image_left_maps_to_facade_offset": "low",
            },
            {
                "photo_index": 2,
                "facade": "left",
                "description": "Exterior access stair is visible.",
                "source": {"kind": "observed", "confidence": 1.0},
                "image_left_maps_to_facade_offset": "low",
            },
        ],
        "known_measurements": [],
        "observations": [
            {
                "id": "access-stair",
                "kind": "stair",
                "facade": "left",
                "certainty": "certain",
                "statement": "Exterior stair exists.",
                "evidence": [
                    {"photo_index": 2, "observation": "Exterior stair is visible."}
                ],
            }
        ],
    }


def _human_fact(observation_id: str = "access-stair") -> dict:
    return {
        "observation_id": observation_id,
        "attribute_name": "stair_topology",
        "value": {
            "minimum_run_count": 2,
            "direction_change": True,
            "turning_node_kind": "turn_or_landing",
        },
        "certainty": "certain",
        "source": {"kind": "user_provided", "confidence": 1.0},
        "statement": "User confirms that the stair changes direction.",
    }


def test_prepare_human_fact_scene_handoff_http_preserves_source_truth() -> None:
    survey = _survey_payload()
    before = deepcopy(survey)

    response = client.post(
        "/api/v1/prepare-human-fact-scene-handoff",
        json={"survey": survey, "human_facts": [_human_fact()]},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert survey == before
    assert payload["source_survey_id"] == survey["id"]
    assert payload["scene_input_survey"]["known_measurements"] == []
    assert payload["scene_input_survey"]["observations"][0]["attributes"]["stair_topology"]["direction_change"] is True
    assert payload["human_facts"][0]["source"]["kind"] == "user_provided"


def test_prepare_human_fact_scene_handoff_http_rejects_unknown_target() -> None:
    response = client.post(
        "/api/v1/prepare-human-fact-scene-handoff",
        json={"survey": _survey_payload(), "human_facts": [_human_fact("missing-stair")]},
    )

    assert response.status_code == 422
    assert "unknown observation" in response.json()["detail"]


def test_prepare_human_fact_scene_handoff_http_rejects_non_user_source() -> None:
    fact = _human_fact()
    fact["source"] = {"kind": "inferred", "confidence": 0.8}

    response = client.post(
        "/api/v1/prepare-human-fact-scene-handoff",
        json={"survey": _survey_payload(), "human_facts": [fact]},
    )

    assert response.status_code == 422
