from fastapi.testclient import TestClient
from brickhouse.api import app


def test_validate_survey_api_preserves_facade_roof_relationship_exactly() -> None:
    payload={"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","facade":"front","certainty":"certain","statement":"gable end plausible","evidence":[{"photo_index":1,"observation":"gable"},{"photo_index":2,"observation":"roof"}],"attributes":{"facade_roof_relationship":"gable_end"},"attribute_certainty":{"facade_roof_relationship":"plausible"}}]}
    roof=TestClient(app).post("/api/v1/validate-survey",json=payload).json()["survey"]["observations"][0]
    assert roof["attributes"]["facade_roof_relationship"]=="gable_end"
