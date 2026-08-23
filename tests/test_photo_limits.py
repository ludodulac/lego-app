from brickhouse import api as api_module
from brickhouse.vision.openai_provider import MAX_VISION_PHOTOS


def test_api_and_vision_providers_share_adaptive_photo_limit() -> None:
    assert api_module.MAX_PHOTOS == MAX_VISION_PHOTOS == 12
