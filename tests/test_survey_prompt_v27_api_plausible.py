from fastapi.testclient import TestClient
from brickhouse.api import app


def test_validate_survey_api_blocks_plausible_multiview_roof_without_shape() -> None:
    payload={"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"plausible","statement":"possible roof","evidence":[{"photo_index":1,"observation":"edge"},{"photo_index":2,"observation":"edge"}]}]}
    body=TestClient(app).post("/api/v1/validate-survey",json=payload).json()
    assert body["valid_for_scene_fusion"] is False
