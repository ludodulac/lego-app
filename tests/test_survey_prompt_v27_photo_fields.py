from pathlib import Path


def test_v27_keeps_photo_view_fields() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    for field in ("photo_index","facade","description","source","image_left_maps_to_facade_offset"):
        assert field in source
