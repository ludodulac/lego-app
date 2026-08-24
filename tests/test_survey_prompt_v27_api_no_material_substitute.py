from fastapi.testclient import TestClient
from brickhouse.api import app


def test_roof_material_does_not_substitute_for_shape_hypothesis() -> None:
    payload={"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"tile roof","evidence":[{"photo_index":1,"observation":"tiles"},{"photo_index":2,"observation":"tiles"}],"attributes":{"exterior_material":"tile"}}]}
    body=TestClient(app).post("/api/v1/validate-survey",json=payload).json()
    assert body["valid_for_scene_fusion"] is False
