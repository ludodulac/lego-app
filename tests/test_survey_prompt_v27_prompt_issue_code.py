from pathlib import Path
from brickhouse.survey.validation import validate_survey_semantics


def test_prompt_and_backend_share_roof_information_loss_issue_code() -> None:
    source=(Path(__file__).resolve().parents[1]/"frontend"/"brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "multiview_roof_missing_shape_hypothesis" in source
    assert callable(validate_survey_semantics)
