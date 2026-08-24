from pathlib import Path


def test_v27_final_audit_repeats_roof_preflight_requirement() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "toute toiture multi-vues passe le PRÉFLIGHT TOITURE MULTI-VUES" in source
