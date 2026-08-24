from pathlib import Path


def test_v27_final_audit_requires_front_photo() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "au moins une photo front" in source
