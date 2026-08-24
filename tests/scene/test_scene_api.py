import json
from pathlib import Path

from fastapi.testclient import TestClient

from brickhouse.api import app


client = TestClient(app)
FIXTURE = Path("tests/fixtures/architectural_scene_real_house_v02.json")
MULTI_FIXTURE = Path("tests/fixtures/architectural_scene_multivolume_house_v02.json")


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _multi_fixture() -> dict:
    return json.loads(MULTI_FIXTURE.read_text(encoding="utf-8"))


def test_validate_scene_accepts_real_house_regression_fixture():
    response = client.post("/api/v1/validate-scene", json=_fixture())
    assert response.status_code == 200
    payload = response.json()
    assert payload["scene"]["schema_version"] == "0.2"
    assert payload["scene"]["volumes"][0]["width"]["value"] == 10.0
    assert payload["projection"]["building"] is not None
    assert payload["projection"]["building"]["schema_version"] == "0.1"
    assert payload["projection"]["building"]["openings"][0]["id"] == "window_front_lower_left"
    assert payload["m0_compatibility"]["buildable"] is True
    codes = {issue["code"] for issue in payload["projection"]["issues"]}
    assert "terrain_not_supported" in codes
    assert "chimney_not_supported" in codes
    assert "platform_not_supported" in codes
    # Hidden stair continuation is deliberately not encoded in the conservative
    # regression Scene, so projection must not report a fabricated stair.
    assert "stair_not_supported" not in codes


def test_validate_scene_rejects_opening_inside_rear_occlusion():
    scene = _fixture()
    scene["openings"].append({
        "id": "invented_rear_window", "type": "window", "volume_id": "volume_main", "facade": "rear",
        "offset_horizontal": 1.0, "offset_vertical": 3.0, "width": 1.0, "height": 1.2,
        "source": {"kind": "inferred", "confidence": 0.3}, "window_style": "simple", "has_sill": True, "has_decorative_surround": False,
    })
    response = client.post("/api/v1/validate-scene", json=scene)
    assert response.status_code == 422
    assert "intersects non-visible facade span" in response.text


def test_validate_scene_rejects_opening_partly_crossing_unknown_boundary():
    scene = _fixture()
    scene["openings"].append({
        "id": "boundary_crossing_window", "type": "window", "volume_id": "volume_main", "facade": "right",
        "offset_horizontal": 8.9, "offset_vertical": 2.0, "width": 0.8, "height": 1.0,
        "source": {"kind": "inferred", "confidence": 0.3}, "window_style": "simple", "has_sill": True, "has_decorative_surround": False,
    })
    response = client.post("/api/v1/validate-scene", json=scene)
    assert response.status_code == 422
    assert "intersects non-visible facade span" in response.text


def test_validate_scene_preserves_multi_volume_projection():
    scene = _fixture()
    second = json.loads(json.dumps(scene["volumes"][0]))
    second["id"] = "volume_second"
    second["position"] = {"x": 10.0, "y": 0.0, "z": 0.0}
    second["width"]["value"] = 2.0
    second["depth"]["value"] = 3.0
    second["height"]["value"] = 2.0
    second["floors"] = 1
    scene["volumes"].append(second)
    response = client.post("/api/v1/validate-scene", json=scene)
    assert response.status_code == 200
    payload = response.json()
    assert payload["projection"]["building"] is not None
    assert len(payload["projection"]["building"]["volumes"]) == 2
    assert payload["m0_compatibility"]["buildable"] is True
    assert any("volumes rectangulaires multiples" in warning for warning in payload["m0_compatibility"]["warnings"])


def test_projected_scene_can_flow_into_current_build_pipeline():
    validated = client.post("/api/v1/validate-scene", json=_fixture())
    assert validated.status_code == 200
    projection = validated.json()["projection"]
    assert projection["building"] is not None
    built = client.post("/api/v1/build", json={"building": projection["building"], "front_width_studs": 48})
    assert built.status_code == 200
    assert built.json()["bom"]["total_parts"] > 0


def test_multivolume_house_scene_flows_from_validation_to_composite_build():
    validated = client.post("/api/v1/validate-scene", json=_multi_fixture())
    assert validated.status_code == 200
    payload = validated.json()
    assert payload["projection"]["building"] is not None
    assert len(payload["projection"]["building"]["volumes"]) == 2
    assert payload["m0_compatibility"]["buildable"] is True
    assert any("toiture plate" in warning for warning in payload["m0_compatibility"]["warnings"])
    built = client.post("/api/v1/build", json={"building": payload["projection"]["building"], "front_width_studs": 48})
    assert built.status_code == 200, built.text
    export = built.json()
    assert export["volume_id"] == "composite"
    assert export["bom"]["total_parts"] > 0
    assert any(part["placement_id"].startswith("volume_main:") for part in export["brick_model"]["parts"])
    assert any(part["placement_id"].startswith("left_low_attached_volume_01:") for part in export["brick_model"]["parts"])
