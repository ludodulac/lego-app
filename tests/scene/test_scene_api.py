import json
from pathlib import Path

from fastapi.testclient import TestClient

from brickhouse.api import app


client = TestClient(app)
FIXTURE = Path("tests/fixtures/architectural_scene_real_house_v02.json")


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_validate_scene_accepts_real_house_regression_fixture():
    response = client.post("/api/v1/validate-scene", json=_fixture())

    assert response.status_code == 200
    payload = response.json()
    assert payload["scene"]["schema_version"] == "0.2"
    assert payload["scene"]["volumes"][0]["width"]["value"] == 10.0
    assert payload["projection"]["building"] is not None
    assert payload["projection"]["building"]["schema_version"] == "0.1"
    assert payload["projection"]["building"]["openings"][0]["id"] == "window_front_lower_left"

    codes = {issue["code"] for issue in payload["projection"]["issues"]}
    assert "terrain_not_supported" in codes
    assert "chimney_not_supported" in codes
    assert "platform_not_supported" in codes
    assert "stair_not_supported" in codes


def test_validate_scene_rejects_opening_inside_rear_occlusion():
    scene = _fixture()
    scene["openings"].append(
        {
            "id": "invented_rear_window",
            "type": "window",
            "volume_id": "volume_main",
            "facade": "rear",
            "offset_horizontal": 1.0,
            "offset_vertical": 3.0,
            "width": 1.0,
            "height": 1.2,
            "source": {"kind": "inferred", "confidence": 0.3},
            "window_style": "simple",
            "has_sill": true,
            "has_decorative_surround": false
        }
    )

    response = client.post("/api/v1/validate-scene", json=scene)
    assert response.status_code == 422
    assert "non-visible facade span" in response.text


def test_projected_scene_can_flow_into_current_build_pipeline():
    validated = client.post("/api/v1/validate-scene", json=_fixture())
    assert validated.status_code == 200
    projection = validated.json()["projection"]
    assert projection["building"] is not None

    built = client.post(
        "/api/v1/build",
        json={"building": projection["building"], "front_width_studs": 48},
    )
    assert built.status_code == 200
    assert built.json()["bom"]["total_parts"] > 0
