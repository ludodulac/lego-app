from pathlib import Path


def test_v27_requires_direct_architectural_survey_json() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "directement validable par `ArchitecturalSurvey`" in source
    assert "JSON valide" in source
