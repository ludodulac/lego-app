from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def test_multiview_nonroof_observation_is_not_subject_to_roof_shape_rule() -> None:
    survey=ArchitecturalSurvey.model_validate({"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"left","description":"left","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"platform","kind":"platform","certainty":"certain","statement":"deck","evidence":[{"photo_index":1,"observation":"edge"},{"photo_index":2,"observation":"edge"}]}]})
    assert validate_survey_semantics(survey)==[]
