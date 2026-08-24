from fastapi.testclient import TestClient
from brickhouse.api import app


def test_validate_survey_api_accepts_plausible_butterfly_roof() -> None:
    payload={"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"butterfly plausible","evidence":[{"photo_index":1,"observation":"valley"},{"photo_index":2,"observation":"valley"}],"attributes":{"roof_type":"butterfly"},"attribute_certainty":{"roof_type":"plausible"}}]}
    assert TestClient(app).post("/api/v1/validate-survey",json=payload).json()["valid_for_scene_fusion"] is True
