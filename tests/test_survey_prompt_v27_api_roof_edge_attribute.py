from fastapi.testclient import TestClient
from brickhouse.api import app


def test_validate_survey_api_preserves_roof_edge_type_exactly() -> None:
    payload={"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"rake plausible","evidence":[{"photo_index":1,"observation":"rake"},{"photo_index":2,"observation":"roof"}],"attributes":{"roof_edge_type":"rake"},"attribute_certainty":{"roof_edge_type":"plausible"}}]}
    roof=TestClient(app).post("/api/v1/validate-survey",json=payload).json()["survey"]["observations"][0]
    assert roof["attributes"]["roof_edge_type"]=="rake"
