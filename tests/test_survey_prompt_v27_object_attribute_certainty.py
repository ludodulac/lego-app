from pathlib import Path


def test_v27_keeps_object_attribute_certainty_separation() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "`certainty` décrit l'existence/identité de l'objet" in source
    assert "`attribute_certainty` décrit chaque propriété incertaine" in source
    assert "Un objet certain ne rend jamais ses attributs certains" in source
