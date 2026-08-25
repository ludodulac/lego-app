import pytest
from pydantic import ValidationError

from brickhouse.survey.models import PhotoView


SOURCE = {"kind": "observed", "confidence": 0.9}


def test_targeted_detail_photo_carries_no_fake_facade_coordinates() -> None:
    photo = PhotoView.model_validate({
        "photo_index": 5,
        "capture_role": "targeted_detail",
        "facade": None,
        "description": "Underside of a terrace and its supports.",
        "source": SOURCE,
        "image_left_maps_to_facade_offset": None,
        "user_note": "Comprendre le dessous de la terrasse.",
    })
    assert photo.facade is None
    assert photo.image_left_maps_to_facade_offset is None
    assert photo.user_note == "Comprendre le dessous de la terrasse."


def test_targeted_detail_rejects_invented_facade_mapping() -> None:
    with pytest.raises(ValidationError, match="must not invent facade coordinates"):
        PhotoView.model_validate({
            "photo_index": 5,
            "capture_role": "targeted_detail",
            "facade": "left",
            "description": "Roof junction detail.",
            "source": SOURCE,
            "image_left_maps_to_facade_offset": "low",
        })


def test_legacy_facade_view_remains_backward_compatible() -> None:
    photo = PhotoView.model_validate({
        "photo_index": 1,
        "facade": "front",
        "description": "Front facade.",
        "source": SOURCE,
    })
    assert photo.capture_role == "facade_view"
    assert photo.facade.value == "front"
    assert photo.image_left_maps_to_facade_offset == "low"
