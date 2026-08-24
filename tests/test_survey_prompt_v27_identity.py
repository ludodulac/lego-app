from pathlib import Path


def test_v27_keeps_observation_ids_as_physical_identity() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "Identité physique = `observations[].id`" in source
    assert "aucune racine `physical_objects`" in source
