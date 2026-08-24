from fastapi.testclient import TestClient
from brickhouse.api import app


def test_validate_survey_api_accepts_plausible_nonmetric_gable_hypothesis() -> None:
    payload={"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"gable plausible","evidence":[{"photo_index":1,"observation":"gable silhouette"},{"photo_index":2,"observation":"slope"}],"attributes":{"roof_type":"gable"},"attribute_certainty":{"roof_type":"plausible"}}]}
    response=TestClient(app).post("/api/v1/validate-survey",json=payload)
    assert response.status_code==200
    assert response.json()["valid_for_scene_fusion"] is True
