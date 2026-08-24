from pathlib import Path


def test_v27_rejects_legacy_external_aliases() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "physical_objects" in source
    assert "canonical_frame x/y/z" in source
    assert "source/evidence chaînes" in source
