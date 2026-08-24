from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def test_multiview_roof_edge_relation_can_preserve_information_without_forced_type() -> None:
    survey=ArchitecturalSurvey.model_validate({"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"edges visible","evidence":[{"photo_index":1,"observation":"rake"},{"photo_index":2,"observation":"edge"}],"attributes":{"roof_edge_type":"rake"},"attribute_certainty":{"roof_edge_type":"plausible"}}]})
    assert validate_survey_semantics(survey)==[]
