from __future__ import annotations

import pytest
from pydantic import ValidationError

from brickhouse.survey import ArchitecturalSurvey


def _survey_payload():
    return {
        "schema_version": "0.1",
        "id": "survey_real_house_photos_1_2",
        "name": "Real house survey photos 1 and 2",
        "photos": [
            {
                "photo_index": 1,
                "facade": "front",
                "description": "Front facade",
                "source": {"kind": "user_provided", "confidence": 0.99},
                "image_left_maps_to_facade_offset": "low",
            },
            {
                "photo_index": 2,
                "facade": "right",
                "description": "Right facade with rising road",
                "source": {"kind": "user_provided", "confidence": 0.99},
                "image_left_maps_to_facade_offset": "low",
            },
        ],
        "observations": [
            {
                "id": "front_surface",
                "kind": "material",
                "facade": "front",
                "certainty": "certain",
                "statement": "Front wall has a light rendered finish.",
                "evidence": [{"photo_index": 1, "observation": "Continuous light rendered wall surface."}],
                "appearance": {
                    "base_material": "rendered_masonry",
                    "nominal_color": "off_white_light_gray",
                    "finish": "matte",
                    "weathering": ["vertical_staining", "darker_lower_zone"],
                    "reproduce_weathering_in_lego": False,
                },
            },
            {
                "id": "front_upper_left_window",
                "kind": "opening",
                "facade": "front",
                "certainty": "certain",
                "statement": "Upper-left front opening is a two-leaf glazed window with a pale mineral surround.",
                "evidence": [{"photo_index": 1, "observation": "Upper-left window is clearly visible."}],
                "opening_visual": {
                    "frame_color": "dark_gray_brown",
                    "leaf_count": 2,
                    "mullion_count": 1,
                    "glazing": "dark_reflective",
                    "sill": "projecting",
                    "surround_material": "mineral_or_stone_like",
                    "surround_color": "beige_pink_light",
                },
            },
            {
                "id": "right_grade",
                "kind": "terrain",
                "facade": "right",
                "certainty": "certain",
                "statement": "Road rises strongly from front toward rear along the right facade.",
                "evidence": [{"photo_index": 2, "observation": "Road edge visibly climbs along wall."}],
            },
        ],
        "representation_policy": {
            "preserve_nominal_materials": True,
            "preserve_opening_composition": True,
            "preserve_architectural_details": True,
            "reproduce_weathering": False,
            "reproduce_temporary_objects": False,
        },
    }


def test_survey_separates_weathering_from_nominal_representation():
    survey = ArchitecturalSurvey.model_validate(_survey_payload())
    surface = survey.observations[0]
    assert surface.appearance is not None
    assert surface.appearance.weathering
    assert surface.appearance.reproduce_weathering_in_lego is False
    assert survey.representation_policy.reproduce_weathering is False


def test_survey_preserves_canonical_photo_mapping():
    survey = ArchitecturalSurvey.model_validate(_survey_payload())
    assert survey.canonical_frame.x_direction == "front_view_left_to_right"
    assert survey.photos[0].image_left_maps_to_facade_offset == "low"
    assert survey.photos[1].facade.value == "right"


def test_survey_carries_exact_user_front_width():
    payload = _survey_payload()
    payload["known_measurements"] = [{
        "kind": "front_width",
        "value": 10.0,
        "units": "m",
        "source": {"kind": "user_provided", "confidence": 0.99},
    }]
    survey = ArchitecturalSurvey.model_validate(payload)
    assert survey.known_measurements[0].kind == "front_width"
    assert survey.known_measurements[0].value == 10.0
    assert survey.known_measurements[0].source.kind.value == "user_provided"


def test_survey_rejects_duplicate_scale_anchor_kind():
    payload = _survey_payload()
    payload["known_measurements"] = [
        {"kind": "front_width", "value": 10.0, "units": "m", "source": {"kind": "user_provided", "confidence": 0.99}},
        {"kind": "front_width", "value": 9.8, "units": "m", "source": {"kind": "user_provided", "confidence": 0.99}},
    ]
    with pytest.raises(ValidationError, match="measurement kinds"):
        ArchitecturalSurvey.model_validate(payload)


def test_survey_rejects_unknown_evidence_photo():
    payload = _survey_payload()
    payload["observations"][0]["evidence"][0]["photo_index"] = 99
    with pytest.raises(ValidationError, match="unknown photo"):
        ArchitecturalSurvey.model_validate(payload)


def test_survey_requires_front_reference_photo():
    payload = _survey_payload()
    payload["photos"][0]["facade"] = "left"
    with pytest.raises(ValidationError, match="canonical front"):
        ArchitecturalSurvey.model_validate(payload)
