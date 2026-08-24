from brickhouse.survey import ArchitecturalSurvey, validate_survey_extension, validate_survey_semantics


def base_survey(observation: dict) -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1", "id": "survey_test", "name": "Survey test",
        "photos": [{"photo_index": 1, "facade": "front", "description": "front", "source": {"kind": "user_provided", "confidence": 0.99}, "image_left_maps_to_facade_offset": "low"}],
        "known_measurements": [{"kind": "front_width", "value": 10.0, "units": "m", "source": {"kind": "user_provided", "confidence": 0.99}}],
        "observations": [observation],
    })


def evidence() -> list[dict]: return [{"photo_index": 1, "observation": "visible"}]
def opening_attributes(**extra) -> dict: return {"physical_object_count": 1, **extra}


def test_grouped_opening_observation_is_rejected() -> None:
    survey = base_survey({"id":"front_openings","kind":"opening","facade":"front","certainty":"certain","statement":"Three front windows","evidence":evidence(),"attributes":{"physical_object_count":3,"semantic_type":"window"}})
    assert "opening_not_single_physical_object" in {issue.code for issue in validate_survey_semantics(survey)}


def test_opening_must_explicitly_declare_single_physical_object() -> None:
    survey=base_survey({"id":"front_window","kind":"opening","facade":"front","certainty":"certain","statement":"Front window","evidence":evidence(),"attributes":{"semantic_type":"window"}})
    assert "opening_not_single_physical_object" in {issue.code for issue in validate_survey_semantics(survey)}


def test_user_confirmed_opening_requires_stable_semantic_role() -> None:
    survey=base_survey({"id":"opening","kind":"opening","facade":"front","certainty":"certain","statement":"Low opening","evidence":evidence(),"attributes":opening_attributes(confirmed_by_user=True,target_building_ownership="proven")})
    assert {issue.code for issue in validate_survey_semantics(survey)}=={"confirmed_opening_missing_semantic_role"}


def test_user_confirmed_workshop_window_can_keep_glass_block_glazing() -> None:
    survey=base_survey({"id":"workshop_window","kind":"opening","facade":"front","certainty":"certain","statement":"Workshop window","evidence":evidence(),"attributes":opening_attributes(confirmed_by_user=True,semantic_role="window",room_role="workshop",target_building_ownership="proven"),"opening_visual":{"glazing":"glass_blocks"}})
    assert validate_survey_semantics(survey)==[]


def test_unproven_opening_ownership_cannot_be_plausible_target_opening() -> None:
    survey=base_survey({"id":"beyond_pole","kind":"opening","facade":"front","certainty":"plausible","statement":"Possible opening beyond boundary","evidence":evidence(),"attributes":opening_attributes(semantic_role="window",target_building_ownership="unproven")})
    assert {issue.code for issue in validate_survey_semantics(survey)}=={"opening_target_ownership_unproven"}


def test_gable_end_rejects_front_eave_terminology() -> None:
    survey=base_survey({"id":"roof","kind":"roof","facade":"front","certainty":"certain","statement":"Front gable","evidence":evidence(),"attributes":{"facade_roof_relationship":"gable_end","roof_edge_type":"eave_across_facade"}})
    assert {issue.code for issue in validate_survey_semantics(survey)}=={"gable_eave_terminology_conflict"}


def test_multiview_roof_cannot_discard_every_shape_hypothesis() -> None:
    payload=base_survey({"id":"roof","kind":"roof","certainty":"certain","statement":"Roof visible but shape discarded","evidence":evidence()}).model_dump(mode="json")
    payload["photos"].append({"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":0.99},"image_left_maps_to_facade_offset":"low"})
    payload["observations"][0]["evidence"].append({"photo_index":2,"observation":"roof edge visible"})
    survey=ArchitecturalSurvey.model_validate(payload)
    assert "multiview_roof_missing_shape_hypothesis" in {issue.code for issue in validate_survey_semantics(survey)}


def test_multiview_roof_may_keep_plausible_gable_without_metrics() -> None:
    payload=base_survey({"id":"roof","kind":"roof","certainty":"certain","statement":"Roof visible","evidence":evidence(),"attributes":{"roof_type":"gable","facade_is_gable":True},"attribute_certainty":{"roof_type":"plausible","facade_is_gable":"plausible"}}).model_dump(mode="json")
    payload["photos"].append({"photo_index":2,"facade":"right","description":"right","source":{"kind":"user_provided","confidence":0.99},"image_left_maps_to_facade_offset":"low"})
    payload["observations"][0]["evidence"].append({"photo_index":2,"observation":"roof edge visible"})
    survey=ArchitecturalSurvey.model_validate(payload)
    assert validate_survey_semantics(survey)==[]


def survey_for_extension() -> ArchitecturalSurvey:
    return base_survey({"id":"front_window","kind":"opening","facade":"front","certainty":"certain","statement":"Front window","evidence":evidence(),"attributes":opening_attributes(semantic_type="window",target_building_ownership="proven")})


def valid_extension(base: ArchitecturalSurvey) -> ArchitecturalSurvey:
    payload=base.model_dump(mode="json")
    payload["photos"].append({"photo_index":2,"facade":"left","description":"left side","source":{"kind":"user_provided","confidence":0.99},"image_left_maps_to_facade_offset":"low"})
    payload["observations"].append({"id":"left_window","kind":"opening","facade":"left","certainty":"certain","statement":"Left window","evidence":[{"photo_index":2,"observation":"visible on new photo"}],"attributes":opening_attributes(semantic_type="window",target_building_ownership="proven")})
    return ArchitecturalSurvey.model_validate(payload)


def test_survey_extension_can_only_append_new_photos_and_observations() -> None:
    base=survey_for_extension(); candidate=valid_extension(base); assert validate_survey_extension(base,candidate)==[]


def test_survey_extension_rejects_rewritten_existing_observation() -> None:
    base=survey_for_extension(); candidate=valid_extension(base); payload=candidate.model_dump(mode="json"); payload["observations"][0]["id"]="renamed_front_window"; rewritten=ArchitecturalSurvey.model_validate(payload)
    assert "survey_extension_observation_removed" in {issue.code for issue in validate_survey_extension(base,rewritten)}


def test_survey_extension_rejects_changed_known_measurement() -> None:
    base=survey_for_extension(); candidate=valid_extension(base); payload=candidate.model_dump(mode="json"); payload["known_measurements"][0]["value"]=9.5; changed=ArchitecturalSurvey.model_validate(payload)
    assert "survey_extension_measurements_changed" in {issue.code for issue in validate_survey_extension(base,changed)}