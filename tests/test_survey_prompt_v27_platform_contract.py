from pathlib import Path


def test_v27_keeps_landing_deck_and_volume_decomposition() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "Une terrasse bois et un palier béton restent deux plateformes distinctes" in source
    assert "stair + platform + relation `connects_to`" in source
    assert "palier→`building_boundary`" in source
