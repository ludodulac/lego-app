from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def test_multiview_roof_facade_relationship_can_preserve_shape_information() -> None:
    survey=ArchitecturalSurvey.model_validate({"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","facade":"front","certainty":"certain","statement":"front relation visible","evidence":[{"photo_index":1,"observation":"gable edge"},{"photo_index":2,"observation":"slope"}],"attributes":{"facade_roof_relationship":"gable_end"},"attribute_certainty":{"facade_roof_relationship":"plausible"}}]})
    assert validate_survey_semantics(survey)==[]
