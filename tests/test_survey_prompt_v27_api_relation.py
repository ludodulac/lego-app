from fastapi.testclient import TestClient
from brickhouse.api import app


def test_validate_survey_api_accepts_plausible_facade_roof_relationship() -> None:
    payload={"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","facade":"front","certainty":"certain","statement":"gable end plausible","evidence":[{"photo_index":1,"observation":"gable edge"},{"photo_index":2,"observation":"slope"}],"attributes":{"facade_roof_relationship":"gable_end"},"attribute_certainty":{"facade_roof_relationship":"plausible"}}]}
    body=TestClient(app).post("/api/v1/validate-survey",json=payload).json()
    assert body["valid_for_scene_fusion"] is True
