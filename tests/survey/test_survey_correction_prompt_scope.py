from pathlib import Path


PROMPT = Path("frontend/brickhouse-survey-correction-v01.txt")


def test_survey_correction_prompt_matches_backend_action_scope_guards() -> None:
    text = PROMPT.read_text(encoding="utf-8")

    assert "merge is NOT automatically correctable in v0.1" in text
    assert "relation reorient is NOT automatically correctable in v0.1" in text
    assert "lower_certainty is eligible only as a true certainty decrease" in text
    assert "reorient is eligible only for observations" in text
    assert "Never invent a substitute action" in text
    assert '"action": "add|remove|lower_certainty|reorient"' in text
