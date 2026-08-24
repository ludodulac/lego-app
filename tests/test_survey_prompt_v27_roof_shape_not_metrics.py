from pathlib import Path


def test_v27_does_not_treat_unknown_metric_roof_as_unknown_shape() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "uniquement parce que sa géométrie métrique est inconnue" in source
