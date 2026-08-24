from fastapi.testclient import TestClient
from brickhouse.api import app


def test_validate_survey_api_accepts_other_without_metric_geometry() -> None:
    payload={"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"other plausible","evidence":[{"photo_index":1,"observation":"roof"},{"photo_index":2,"observation":"roof"}],"attributes":{"roof_type":"other"},"attribute_certainty":{"roof_type":"plausible"}}]}
    roof=TestClient(app).post("/api/v1/validate-survey",json=payload).json()["survey"]["observations"][0]
    assert set(roof["attributes"])=={"roof_type"}
