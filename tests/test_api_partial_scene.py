import json
from pathlib import Path

from fastapi.testclient import TestClient

from brickhouse.api import app


client = TestClient(app)
FIXTURE = Path("tests/fixtures/brickhouse_scene_current.json")


def _scene() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_build_scene_partial_returns_first_trustworthy_bricks() -> None:
    response = client.post(
        "/api/v1/build-scene",
        json={"scene": _scene(), "front_width_studs": 48, "allow_partial": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["brick_model"]["parts"]
    assert any(part["component"] == "wall" for part in payload["brick_model"]["parts"])
    assert not any(part["component"] == "roof" for part in payload["brick_model"]["parts"])
    assert payload["bom"]["total_parts"] == len(payload["brick_model"]["parts"])
    assert payload["assembly_plan"]["total_parts"] == payload["bom"]["total_parts"]
    assert payload["assembly_plan"]["total_steps"] > 0
    assert "partial_preview_roof_omitted" in {
        issue["code"] for issue in payload["fidelity_issues"]
    }


def test_build_scene_remains_strict_by_default() -> None:
    response = client.post(
        "/api/v1/build-scene",
        json={"scene": _scene(), "front_width_studs": 48},
    )

    assert response.status_code == 422
