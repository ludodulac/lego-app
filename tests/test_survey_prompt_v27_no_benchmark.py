from pathlib import Path


def test_v27_explicitly_forbids_benchmark_specific_assumptions() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "aucune caractéristique héritée d'un benchmark particulier" in source
    assert "Aucun nombre d’ouvertures, type de toiture" in source
