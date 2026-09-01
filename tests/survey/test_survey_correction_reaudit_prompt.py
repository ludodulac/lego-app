from pathlib import Path


PROMPT = Path("frontend/brickhouse-survey-correction-reaudit-v01.txt")


def test_targeted_reaudit_prompt_stays_bounded_and_non_mutating() -> None:
    text = PROMPT.read_text(encoding="utf-8")

    assert "You do NOT perform a new full independent SurveyAudit" in text
    assert "you do NOT mutate the candidate" in text
    assert "SCOPE IS AUTHORITATIVE" in text
    assert "Do not report unrelated omissions" in text
    assert "target_type observation or relation" in text
    assert '"kind": "survey_correction_reaudit"' in text
    assert "no survey/photo-level finding was emitted" in text
