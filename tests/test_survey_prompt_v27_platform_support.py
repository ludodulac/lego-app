from pathlib import Path


def test_v27_does_not_turn_support_posts_into_platforms() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "pas dans une fausse deuxième plateforme" in source
