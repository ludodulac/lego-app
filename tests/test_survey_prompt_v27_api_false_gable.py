from fastapi.testclient import TestClient
from brickhouse.api import app


def test_explicit_plausible_non_gable_facade_is_still_shape_information() -> None:
    payload={"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"front likely not gable","evidence":[{"photo_index":1,"observation":"eave"},{"photo_index":2,"observation":"roof"}],"attributes":{"facade_is_gable":False},"attribute_certainty":{"facade_is_gable":"plausible"}}]}
    body=TestClient(app).post("/api/v1/validate-survey",json=payload).json()
    assert body["valid_for_scene_fusion"] is True
