import json
from pathlib import Path
from types import SimpleNamespace

from brickhouse.vision.openai_provider import PhotoInput, analyze_building_photos


REFERENCE = Path("docs/examples/building-model-simple-house.json")


class FakeResponses:
    def __init__(self, output_text: str):
        self.output_text = output_text
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(output_text=self.output_text)


class FakeClient:
    def __init__(self, output_text: str):
        self.responses = FakeResponses(output_text)


def _output() -> str:
    building = json.loads(REFERENCE.read_text(encoding="utf-8"))
    building["metadata"]["created_from"] = "photo_analysis"
    building["metadata"]["notes"] = "proposition vision"
    return json.dumps({
        "schema_version": "0.1",
        "building": building,
        "questions": [{
            "id": "q_rear",
            "question": "L’arrière est-il un mur simple ?",
            "reason": "L’arrière n’est pas visible.",
            "importance": "recommended"
        }],
        "assumptions": ["Arrière rectangulaire simple."],
        "confidence": 0.71,
        "needs_confirmation": True
    })


def test_provider_sends_multiple_images_as_data_urls_and_parses_contract():
    client = FakeClient(_output())
    result = analyze_building_photos(
        [
            PhotoInput(content=b"front", media_type="image/jpeg", filename="front.jpg"),
            PhotoInput(content=b"left", media_type="image/png", filename="left.png"),
        ],
        user_notes="Terrasse à gauche",
        known_front_width_m=10.0,
        client=client,
        model="test-vision-model",
    )
    assert result.building.metadata.created_from == "photo_analysis"
    assert result.needs_confirmation is True
    kwargs = client.responses.kwargs
    assert kwargs["model"] == "test-vision-model"
    content = kwargs["input"][0]["content"]
    images = [item for item in content if item["type"] == "input_image"]
    assert len(images) == 2
    assert images[0]["image_url"].startswith("data:image/jpeg;base64,")
    assert images[1]["image_url"].startswith("data:image/png;base64,")
    assert kwargs["text"]["format"]["type"] == "json_schema"


def test_provider_rejects_invalid_photo_contract_before_network():
    client = FakeClient(_output())
    try:
        analyze_building_photos([], client=client)
    except ValueError as exc:
        assert "between 1 and 6" in str(exc)
    else:
        raise AssertionError("expected ValueError")
    assert client.responses.kwargs is None
