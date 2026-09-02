from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def _base_payload() -> dict:
    return {
        "schema_version": "0.1",
        "id": "survey-shape-normalization",
        "name": "Survey",
        "canonical_frame": {
            "front_facade": "front",
            "x_direction": "front_view_left_to_right",
            "y_direction": "front_to_rear",
            "z_direction": "bottom_to_top",
        },
        "photos": [
            {
                "photo_index": 1,
                "facade": "front",
                "description": "Front",
                "source": {"kind": "user_provided", "confidence": 1.0},
                "image_left_maps_to_facade_offset": "low",
            }
        ],
        "known_measurements": [],
        "observations": [],
        "relations": [],
        "notes": None,
    }


def test_legacy_representation_policy_list_normalizes_to_safe_defaults() -> None:
    payload = _base_payload()
    payload["representation_policy"] = [
        "preserve_nominal_materials",
        "preserve_opening_composition",
        "preserve_architectural_details",
        "reproduce_weathering",
        "reproduce_temporary_objects",
    ]

    survey = ArchitecturalSurvey.model_validate(payload)

    assert survey.representation_policy.preserve_nominal_materials is True
    assert survey.representation_policy.preserve_opening_composition is True
    assert survey.representation_policy.preserve_architectural_details is True
    assert survey.representation_policy.reproduce_weathering is False
    assert survey.representation_policy.reproduce_temporary_objects is False


def test_secondary_volume_kind_normalizes_without_changing_observation_facts() -> None:
    payload = _base_payload()
    payload["observations"] = [
        {
            "id": "rear-low-volume-1",
            "kind": "secondary_volume",
            "facade": "rear",
            "certainty": "certain",
            "statement": "A low attached secondary volume is visible at the rear.",
            "evidence": [{"photo_index": 1, "observation": "Attached low volume visible."}],
            "attributes": {"physical_object_count": 1, "attachment": "attached"},
        }
    ]

    survey = ArchitecturalSurvey.model_validate(payload)
    volume = survey.observations[0]

    assert volume.kind.value == "volume"
    assert volume.id == "rear-low-volume-1"
    assert volume.statement == "A low attached secondary volume is visible at the rear."
    assert volume.attributes == {"physical_object_count": 1, "attachment": "attached"}
    assert volume.evidence[0].observation == "Attached low volume visible."
    assert validate_survey_semantics(survey) == []


def test_unknown_observation_kind_is_not_silently_repaired() -> None:
    payload = _base_payload()
    payload["observations"] = [
        {
            "id": "invented-kind",
            "kind": "annex_guess",
            "certainty": "plausible",
            "statement": "Unsupported free-form category.",
            "evidence": [{"photo_index": 1, "observation": "Some shape is visible."}],
        }
    ]

    try:
        ArchitecturalSurvey.model_validate(payload)
    except Exception:
        pass
    else:
        raise AssertionError("unknown observation kinds must remain invalid")


def test_unproven_opening_placeholder_and_qualitative_ranks_are_normalized() -> None:
    payload = _base_payload()
    payload["representation_policy"] = ["preserve_nominal_materials"]
    payload["observations"] = [
        {
            "id": "obs-unknown-opening",
            "kind": "opening",
            "facade": "front",
            "certainty": "certain",
            "statement": "An opening is visible but its subtype is unknown.",
            "evidence": [{"photo_index": 1, "observation": "Visible opening."}],
            "attributes": {
                "physical_object_count": 1,
                "semantic_type": "opening",
                "facade_horizontal_rank": "low",
                "facade_vertical_rank": "high",
            },
            "attribute_certainty": {"semantic_type": "unproven"},
        }
    ]

    survey = ArchitecturalSurvey.model_validate(payload)
    opening = survey.observations[0]

    assert "semantic_type" not in opening.attributes
    assert "semantic_type" not in opening.attribute_certainty
    assert opening.attributes["physical_object_count"] == 1
    assert opening.attributes["facade_horizontal_rank"] == 1
    assert opening.attributes["facade_vertical_rank"] == 2
    assert validate_survey_semantics(survey) == []


def test_unknown_representation_policy_name_is_not_silently_repaired() -> None:
    payload = _base_payload()
    payload["representation_policy"] = ["invent_missing_geometry"]

    try:
        ArchitecturalSurvey.model_validate(payload)
    except Exception:
        pass
    else:
        raise AssertionError("unknown representation policy list must remain invalid")
