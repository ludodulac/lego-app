from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def test_new_roof_preflight_does_not_remove_gable_eave_conflict_guard() -> None:
    survey=ArchitecturalSurvey.model_validate({"schema_version":"0.1","id":"s","name":"s","photos":[{"photo_index":1,"facade":"front","description":"front","source":{"kind":"user_provided","confidence":1},"image_left_maps_to_facade_offset":"low"}],"observations":[{"id":"roof","kind":"roof","facade":"front","certainty":"certain","statement":"conflict","evidence":[{"photo_index":1,"observation":"edge"}],"attributes":{"facade_roof_relationship":"gable_end","roof_edge_type":"eave_across_facade"}}]})
    assert "gable_eave_terminology_conflict" in {i.code for i in validate_survey_semantics(survey)}
