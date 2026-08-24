from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def test_single_view_roof_without_shape_hypothesis_remains_allowed() -> None:
    survey=ArchitecturalSurvey.model_validate({"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"edge visible","evidence":[{"photo_index":1,"observation":"edge only"}]}]})
    assert validate_survey_semantics(survey)==[]
