from pathlib import Path


def test_v27_forbids_empty_multiview_roof_attributes_as_metric_fallback() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert 'Une toiture multi-vues ne doit pas sortir avec `attributes:{}`' in source
