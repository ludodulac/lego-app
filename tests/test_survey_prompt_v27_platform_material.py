from pathlib import Path


def test_v27_keeps_distinct_platforms_when_materials_differ() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "terrasse bois et un palier béton restent deux plateformes distinctes" in source
