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


def test_health_endpoint(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("RENDER_GIT_COMMIT", raising=False)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "brickhouse-engine", "vision_enabled": False, "engine_revision": "local"}


def test_health_reports_render_revision(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abc123")
    assert client.get("/health").json()["engine_revision"] == "abc123"


def test_health_reports_vision_when_key_is_configured(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert client.get("/health").json()["vision_enabled"] is True


def test_capabilities_explain_photo_readiness(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("RENDER_GIT_COMMIT", "rev-1")
    payload = client.get("/api/v1/capabilities").json()
    assert payload == {
        "engine_ready": True,
        "photo_analysis_ready": False,
        "photo_provider": None,
        "max_photos": 6,
        "supported_photo_types": ["image/jpeg", "image/png", "image/webp"],
        "max_photo_bytes": 12 * 1024 * 1024,
        "engine_revision": "rev-1",
    }
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    enabled = client.get("/api/v1/capabilities").json()
    assert enabled["photo_analysis_ready"] is True
    assert enabled["photo_provider"] == "openai"


def test_build_endpoint_returns_canonical_export(monkeypatch):
    monkeypatch.setenv("RENDER_GIT_COMMIT", "test-revision")
    response = client.post("/api/v1/build", json={"building": _reference_building(), "front_width_studs": 48})
    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "0.1"
    assert payload["building_id"] == "building_simple_house_001"
    assert payload["metadata"]["engine_revision"] == "test-revision"
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


def test_photo_analysis_is_disabled_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    response = client.post(
        "/api/v1/analyze-photos",
        files=[("photos", ("front.jpg", b"fake-jpeg-front", "image/jpeg"))],
    )
    assert response.status_code == 503
    assert "pas activée" in response.json()["detail"]


def test_photo_analysis_endpoint_returns_mocked_structured_result(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
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


def test_photo_proposal_can_flow_directly_into_brick_build(monkeypatch):
    """Contract test for the MVP path: photos -> BuildingModel -> BrickExportBundle."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("RENDER_GIT_COMMIT", "photo-mvp")
    monkeypatch.setattr(api_module, "analyze_building_photos", lambda *args, **kwargs: _analysis_result())
    analyzed = client.post(
        "/api/v1/analyze-photos",
        files=[("photos", ("front.jpg", b"fake-jpeg-front", "image/jpeg"))],
        data={"known_front_width_m": "10.0"},
    )
    assert analyzed.status_code == 200
    proposal = analyzed.json()["building"]
    built = client.post("/api/v1/build", json={"building": proposal, "front_width_studs": 48})
    assert built.status_code == 200
    export = built.json()
    assert export["building_id"] == proposal["id"]
    assert export["metadata"]["engine_revision"] == "photo-mvp"
    assert export["bom"]["total_parts"] == len(export["brick_model"]["parts"])
    assert export["assembly_plan"]["total_parts"] == export["bom"]["total_parts"]
    assert export["assembly_plan"]["total_steps"] > 0


def test_photo_analysis_rejects_unsupported_file_type(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(api_module, "analyze_building_photos", lambda *args, **kwargs: _analysis_result())
    response = client.post(
        "/api/v1/analyze-photos",
        files=[("photos", ("plan.pdf", b"pdf", "application/pdf"))],
    )
    assert response.status_code == 415


def test_photo_analysis_rejects_too_many_photos(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(api_module, "analyze_building_photos", lambda *args, **kwargs: _analysis_result())
    files = [("photos", (f"p{i}.jpg", b"photo", "image/jpeg")) for i in range(7)]
    response = client.post("/api/v1/analyze-photos", files=files)
    assert response.status_code == 422
