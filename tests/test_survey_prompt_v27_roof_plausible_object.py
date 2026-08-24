from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def test_multiview_plausible_roof_also_cannot_silently_drop_shape_information() -> None:
    survey=ArchitecturalSurvey.model_validate({"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"plausible","statement":"possible roof","evidence":[{"photo_index":1,"observation":"edge"},{"photo_index":2,"observation":"edge"}]}]})
    assert "multiview_roof_missing_shape_hypothesis" in {i.code for i in validate_survey_semantics(survey)}
