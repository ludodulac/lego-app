from brickhouse.survey import ArchitecturalSurvey, validate_survey_extension, validate_survey_semantics


def _base() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "survey_elements",
        "name": "Survey elements",
        "photos": [{
            "photo_index": 1,
            "facade": "front",
            "description": "front",
            "source": {"kind": "user_provided", "confidence": 0.99},
            "image_left_maps_to_facade_offset": "low",
        }],
        "known_measurements": [{
            "kind": "front_width",
            "value": 10.0,
            "units": "m",
            "source": {"kind": "user_provided", "confidence": 0.99},
        }],
        "observations": [],
    })


def _extended(kind: str, observation_id: str) -> ArchitecturalSurvey:
    base = _base()
    payload = base.model_dump(mode="json")
    payload["photos"].append({
        "photo_index": 2,
        "facade": "left",
        "description": "left",
        "source": {"kind": "user_provided", "confidence": 0.99},
        "image_left_maps_to_facade_offset": "low",
    })
    payload["observations"].append({
        "id": observation_id,
        "kind": kind,
        "facade": "left",
        "certainty": "certain",
        "statement": observation_id,
        "evidence": [{"photo_index": 2, "observation": "visible"}],
        "attributes": {
            "architectural_kind": kind,
            "target_building_ownership": "proven",
        },
    })
    return ArchitecturalSurvey.model_validate(payload)


def test_platform_is_native_survey_kind() -> None:
    base = _base()
    assert validate_survey_extension(base, _extended("platform", "rear_deck_01")) == []


def test_stair_is_native_survey_kind() -> None:
    base = _base()
    assert validate_survey_extension(base, _extended("stair", "left_exterior_stair_01")) == []


def test_attached_secondary_volume_is_native_survey_kind() -> None:
    base = _base()
    assert validate_survey_extension(base, _extended("volume", "left_low_attached_volume_01")) == []


def test_target_building_architectural_element_cannot_be_context() -> None:
    survey = _extended("platform", "rear_deck_01")
    payload = survey.model_dump(mode="json")
    payload["observations"][0]["kind"] = "context"
    downgraded = ArchitecturalSurvey.model_validate(payload)
    codes = {issue.code for issue in validate_survey_semantics(downgraded)}
    assert "target_building_element_downgraded_to_context" in codes
    assert "architectural_kind_mismatch" in codes
