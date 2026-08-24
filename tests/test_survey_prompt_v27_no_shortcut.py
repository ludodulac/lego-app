from pathlib import Path


def test_v27_does_not_replace_landing_connection_with_stair_building_shortcut() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "Ne simplifie pas en escalier→bâtiment" in source
