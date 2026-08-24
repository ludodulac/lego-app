from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def test_duplicate_evidence_from_one_photo_does_not_trigger_multiview_roof_rule() -> None:
    survey=ArchitecturalSurvey.model_validate({"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","certainty":"certain","statement":"two notes same view","evidence":[{"photo_index":1,"observation":"edge"},{"photo_index":1,"observation":"silhouette"}]}]})
    assert validate_survey_semantics(survey)==[]
