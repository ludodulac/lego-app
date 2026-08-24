from pathlib import Path


def test_v27_final_audit_requires_statement_and_evidence() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "chaque observation a statement + evidence" in source
