import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def test_multiview_roof_information_loss_is_error_not_warning() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    survey=ArchitecturalSurvey.model_validate(payload)
    issue=next(i for i in validate_survey_semantics(survey) if i.code=="multiview_roof_missing_shape_hypothesis")
    assert issue.severity=="error"
