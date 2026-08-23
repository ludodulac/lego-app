from fastapi.testclient import TestClient

from brickhouse.api import app


client = TestClient(app)


def _scene_payload() -> dict:
    return {
        "schema_version": "0.2",
        "id": "scene-api-rich",
        "name": "Scene API rich build",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 1}},
            "depth": {"value": 8, "source": {"kind": "inferred", "confidence": .6}},
            "height": {"value": 6, "source": {"kind": "inferred", "confidence": .6}},
            "floors": 2,
            "source": {"kind": "inferred", "confidence": .6},
        }],
        "terrain": {"kind": "facade_grade_profiles", "profiles": [{
            "facade": "left",
            "start_elevation": 0,
            "end_elevation": .2,
            "outward_extent": 1.5,
            "source": {"kind": "inferred", "confidence": .5},
        }]},
        "platforms": [{
            "id": "deck",
            "position": {"x": -2, "y": 3, "z": 2},
            "width": 2,
            "depth": 3,
            "thickness": .2,
            "material": "timber",
            "deck_board_direction": "y",
            "supports": [],
            "edges": {
                "x_min": {"treatment": "open_railing", "access_spans": []},
                "x_max": {"treatment": "wall_attached", "access_spans": []},
                "y_min": {"treatment": "open_railing", "access_spans": [{"from": .5, "to": 1.5}]},
                "y_max": {"treatment": "open_railing", "access_spans": []},
            },
            "source": {"kind": "inferred", "confidence": .6},
        }],
        "stairs": [{
            "id": "stair",
            "start": {"x": -1, "y": 1, "z": 0},
            "end": {"x": -1, "y": 3, "z": 2},
            "width": 1,
            "material": "concrete",
            "left_edge": "solid_parapet",
            "right_edge": "none",
            "source": {"kind": "inferred", "confidence": .5},
        }],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "dark_brown"},
        },
    }


def test_build_scene_endpoint_preserves_scene_only_architecture(monkeypatch) -> None:
    monkeypatch.setenv("RENDER_GIT_COMMIT", "scene-aware-test")
    response = client.post("/api/v1/build-scene", json={"scene": _scene_payload(), "front_width_studs": 48})
    assert response.status_code == 200, response.text
    payload = response.json()
    ids = {part["placement_id"] for part in payload["brick_model"]["parts"]}
    categories = {part["category"] for part in payload["brick_model"]["parts"]}
    assert any(value.startswith("scene-platform:deck:") for value in ids)
    assert any(value.startswith("scene-stair:stair:") for value in ids)
    assert "terrain" in categories
    assert payload["metadata"]["engine_revision"] == "scene-aware-test"
    assert payload["bom"]["total_parts"] == len(payload["brick_model"]["parts"])
    assert not any(issue.get("code") in {"terrain_not_supported", "platform_not_supported", "stair_not_supported"} for issue in payload.get("fidelity_issues", []))
