from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def test_multiview_gable_hypothesis_needs_no_pitch_or_height() -> None:
    survey=ArchitecturalSurvey.model_validate({"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"},{"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"gable plausible","evidence":[{"photo_index":1,"observation":"gable silhouette"},{"photo_index":2,"observation":"slope"}],"attributes":{"roof_type":"gable"},"attribute_certainty":{"roof_type":"plausible"}}]})
    assert validate_survey_semantics(survey)==[]
