from pathlib import Path


def test_v27_lists_all_scene_supported_opening_semantic_types() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    for value in ("window","door","door_or_glazed_door","glazed_door_or_large_glazed_opening","garage_door"):
        assert value in source
