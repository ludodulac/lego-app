from fastapi.testclient import TestClient
from brickhouse.api import app


def test_unrelated_roof_attribute_certainty_does_not_satisfy_shape_preflight() -> None:
    payload={"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"roof","evidence":[{"photo_index":1,"observation":"roof"},{"photo_index":2,"observation":"roof"}],"attributes":{"material":"tile"},"attribute_certainty":{"material":"plausible"}}]}
    body=TestClient(app).post("/api/v1/validate-survey",json=payload).json()
    assert body["valid_for_scene_fusion"] is False
