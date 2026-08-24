from pathlib import Path


def test_v27_keeps_unknown_regions_unknown() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "Une zone cachée reste inconnue" in source
