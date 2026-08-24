from pathlib import Path


def test_v27_keeps_sourceinfo_and_evidence_object_shapes() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert '"kind":"user_provided|observed|inferred|generated_default"' in source
    assert '"photo_index":1, "observation":"..."' in source
    assert "jamais une chaîne" in source
