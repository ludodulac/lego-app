import json
from pathlib import Path

import httpx

from brickhouse.vision.gemini_provider import MAX_GEMINI_INLINE_RAW_BYTES, analyze_building_photos_gemini
from brickhouse.vision.openai_provider import PhotoInput

REFERENCE = Path("docs/examples/building-model-simple-house.json")


def _provider_dict() -> dict:
    building = json.loads(REFERENCE.read_text(encoding="utf-8"))
    building["metadata"]["created_from"] = "photo_analysis"
    return {
        "schema_version": "0.3",
        "building": building,
        "questions": [],
        "assumptions": ["rear inferred"],
        "confidence": 0.76,
        "needs_confirmation": False,
        "scale_basis": "known front width 10m",
        "proportion_evidence": [],
        "m0_compatibility": None,
    }


def _provider_output() -> str:
    return json.dumps(_provider_dict())


def _response(text: str) -> httpx.Response:
    return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": text}]}}]})


def test_gemini_sends_multiple_inline_images_and_json_schema():
    captured = {}
    def handler(request: httpx.Request):
        captured["url"] = str(request.url)
        captured["key"] = request.headers.get("x-goog-api-key")
        captured["body"] = json.loads(request.content)
        return _response(_provider_output())

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = analyze_building_photos_gemini(
        [
            PhotoInput(content=b"front", media_type="image/jpeg", filename="front.jpg"),
            PhotoInput(content=b"side", media_type="image/png", filename="side.png"),
        ],
        user_notes="garage at right",
        known_front_width_m=10,
        client=client,
        model="gemini-test-model",
        api_key="test-gemini-key",
    )
    assert result.building.metadata.created_from == "photo_analysis"
    assert captured["key"] == "test-gemini-key"
    assert "/models/gemini-test-model:generateContent" in captured["url"]
    body = captured["body"]
    assert "perspective" in body["system_instruction"]["parts"][0]["text"].lower()
    parts = body["contents"][0]["parts"]
    inline = [part["inline_data"] for part in parts if "inline_data" in part]
    assert len(inline) == 2
    assert inline[0]["mime_type"] == "image/jpeg"
    assert inline[1]["mime_type"] == "image/png"
    config = body["generationConfig"]
    assert config["responseMimeType"] == "application/json"
    assert config["responseJsonSchema"]["type"] == "object"


def test_gemini_accepts_accidental_json_markdown_fence():
    calls = 0
    def handler(request: httpx.Request):
        nonlocal calls
        calls += 1
        return _response("```json\n" + _provider_output() + "\n```")
    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = analyze_building_photos_gemini(
        [PhotoInput(content=b"front", media_type="image/jpeg", filename="front.jpg")],
        client=client, model="test-model", api_key="test-key",
    )
    assert result.confidence == 0.76
    assert calls == 1


def test_gemini_repairs_schema_invalid_candidate_once_without_resending_images():
    valid = _provider_dict()
    invalid = {**valid, "confidence": 4.2}
    bodies = []
    def handler(request: httpx.Request):
        bodies.append(json.loads(request.content))
        return _response(json.dumps(invalid if len(bodies) == 1 else valid))
    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = analyze_building_photos_gemini(
        [PhotoInput(content=b"front", media_type="image/jpeg", filename="front.jpg")],
        client=client, model="test-model", api_key="test-key",
    )
    assert result.confidence == 0.76
    assert len(bodies) == 2
    repair_text = bodies[1]["contents"][0]["parts"][0]["text"]
    assert "VALIDATION ERRORS" in repair_text
    assert "Preserve all architectural observations" in repair_text
    assert "inline_data" not in json.dumps(bodies[1])


def test_gemini_fails_after_one_unsuccessful_repair():
    invalid = {**_provider_dict(), "confidence": 4.2}
    calls = 0
    def handler(request: httpx.Request):
        nonlocal calls
        calls += 1
        return _response(json.dumps(invalid))
    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        analyze_building_photos_gemini(
            [PhotoInput(content=b"front", media_type="image/jpeg", filename="front.jpg")],
            client=client, model="test-model", api_key="test-key",
        )
    except ValueError as exc:
        assert "after repair" in str(exc)
    else:
        raise AssertionError("expected ValueError")
    assert calls == 2


def test_gemini_rejects_inline_payload_that_would_exceed_safe_limit():
    photo = PhotoInput(content=b"x" * (MAX_GEMINI_INLINE_RAW_BYTES + 1), media_type="image/jpeg", filename="huge.jpg")
    try:
        analyze_building_photos_gemini([photo], api_key="test")
    except ValueError as exc:
        assert "14 Mo" in str(exc)
    else:
        raise AssertionError("expected ValueError")
