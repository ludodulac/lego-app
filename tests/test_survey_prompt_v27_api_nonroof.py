from fastapi.testclient import TestClient
from brickhouse.api import app


def test_validate_survey_api_does_not_apply_roof_rule_to_platform() -> None:
    payload={"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"left","description":"left","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"p","kind":"platform","certainty":"certain","statement":"platform","evidence":[{"photo_index":1,"observation":"edge"},{"photo_index":2,"observation":"edge"}]}]}
    body=TestClient(app).post("/api/v1/validate-survey",json=payload).json()
    assert body["valid_for_scene_fusion"] is True
