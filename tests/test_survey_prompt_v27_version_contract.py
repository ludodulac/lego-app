from pathlib import Path


def test_active_survey_prompt_is_v27() -> None:
    source = (Path(__file__).resolve().parents[1] / "frontend" / "brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert source.startswith("BRICKHOUSE — PROMPT DE RELEVÉ ARCHITECTURAL v2.7")
