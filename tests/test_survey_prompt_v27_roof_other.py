from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def test_multiview_roof_explicit_other_hypothesis_is_not_silent_loss() -> None:
    survey=ArchitecturalSurvey.model_validate({"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"shape seen but not standard","evidence":[{"photo_index":1,"observation":"edge"},{"photo_index":2,"observation":"edge"}],"attributes":{"roof_type":"other"},"attribute_certainty":{"roof_type":"plausible"}}]})
    assert validate_survey_semantics(survey)==[]
