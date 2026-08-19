import json
from pathlib import Path

from fastapi.testclient import TestClient

import brickhouse.api as api_module
from brickhouse.api import app
from brickhouse.building.models import BuildingModel
from brickhouse.vision.models import ClarificationQuestion, PhotoAnalysisResult


client = TestClient(app)
REFERENCE = Path("docs/examples/building-model-simple-house.json")


def _reference_building() -> dict:
    return json.loads(REFERENCE.read_text(encoding="utf-8"))


def _analysis_result() -> PhotoAnalysisResult:
    building_data = _reference_building()
    building_data["metadata"]["created_from"] = "photo_analysis"
    return PhotoAnalysisResult(
        building=BuildingModel.model_validate(building_data),
        questions=[ClarificationQuestion(id="q1", question="Quelle est la largeur réelle de la façade ?", reason="Échelle absolue incertaine", importance="recommended")],
        assumptions=["L’arrière est supposé rectangulaire car il n’est pas visible."],
        confidence=0.74,
        needs_confirmation=True,
    )


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "brickhouse-engine"}


def test_build_endpoint_returns_canonical_export():
    response = client.post("/api/v1/build", json={"building": _reference_building(), "front_width_studs": 48})
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
    response = client.post("/api/v1/build", json={"building": _reference_building(), "front_width_studs": 0})
    assert response.status_code == 422


def test_photo_analysis_endpoint_returns_mocked_structured_result(monkeypatch):
    captured = {}
    def fake_analyze(photos, *, user_notes="", known_front_width_m=None):
        captured["count"] = len(photos)
        captured["notes"] = user_notes
        captured["width"] = known_front_width_m
        return _analysis_result()
    monkeypatch.setattr(api_module, "analyze_building_photos", fake_analyze)
    response = client.post(
        "/api/v1/analyze-photos",
        files=[
            ("photos", ("front.jpg", b"fake-jpeg-front", "image/jpeg")),
            ("photos", ("side.png", b"fake-png-side", "image/png")),
        ],
        data={"user_notes": "Terrasse à gauche", "known_front_width_m": "10.2"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["building"]["metadata"]["created_from"] == "photo_analysis"
    assert payload["needs_confirmation"] is True
    assert payload["questions"][0]["importance"] == "recommended"
    assert captured == {"count": 2, "notes": "Terrasse à gauche", "width": 10.2}


def test_photo_analysis_rejects_unsupported_file_type(monkeypatch):
    monkeypatch.setattr(api_module, "analyze_building_photos", lambda *args, **kwargs: _analysis_result())
    response = client.post(
        "/api/v1/analyze-photos",
        files=[("photos", ("plan.pdf", b"pdf", "application/pdf"))],
    )
    assert response.status_code == 415


def test_photo_analysis_rejects_too_many_photos(monkeypatch):
    monkeypatch.setattr(api_module, "analyze_building_photos", lambda *args, **kwargs: _analysis_result())
    files = [("photos", (f"p{i}.jpg", b"photo", "image/jpeg")) for i in range(7)]
    response = client.post("/api/v1/analyze-photos", files=files)
    assert response.status_code == 422
