from fastapi.testclient import TestClient
from brickhouse.api import app


def test_validate_survey_api_preserves_false_facade_is_gable_value() -> None:
    payload={"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"not gable plausible","evidence":[{"photo_index":1,"observation":"eave"},{"photo_index":2,"observation":"roof"}],"attributes":{"facade_is_gable":False},"attribute_certainty":{"facade_is_gable":"plausible"}}]}
    roof=TestClient(app).post("/api/v1/validate-survey",json=payload).json()["survey"]["observations"][0]
    assert roof["attributes"]["facade_is_gable"] is False
