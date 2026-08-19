import json
from pathlib import Path

from fastapi.testclient import TestClient

from brickhouse.api import app


client = TestClient(app)
REFERENCE = Path("docs/examples/building-model-simple-house.json")


def _reference_building() -> dict:
    return json.loads(REFERENCE.read_text(encoding="utf-8"))


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "brickhouse-engine"}


def test_build_endpoint_returns_canonical_export():
    response = client.post(
        "/api/v1/build",
        json={"building": _reference_building(), "front_width_studs": 48},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "0.1"
    assert payload["building_id"] == "building_simple_house_001"
    assert payload["bom"]["total_parts"] == len(payload["brick_model"]["parts"])
    assert payload["assembly_plan"]["total_parts"] == payload["bom"]["total_parts"]
    assert any(part["part_id"].startswith("BRICK_SLOPED_33_") for part in payload["brick_model"]["parts"])


def test_build_endpoint_uses_default_front_width():
    response = client.post("/api/v1/build", json={"building": _reference_building()})
    assert response.status_code == 200
    assert response.json()["brick_model"]["width_studs"] == 48


def test_invalid_building_model_returns_422():
    broken = _reference_building()
    broken["volumes"][0]["width"] = -1
    response = client.post("/api/v1/build", json={"building": broken})
    assert response.status_code == 422


def test_invalid_target_width_returns_422():
    response = client.post(
        "/api/v1/build",
        json={"building": _reference_building(), "front_width_studs": 0},
    )
    assert response.status_code == 422
