import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics


def test_roof_information_loss_message_requests_hypothesis_not_metrics() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8")); survey=ArchitecturalSurvey.model_validate(payload)
    issue=next(i for i in validate_survey_semantics(survey) if i.code=="multiview_roof_missing_shape_hypothesis")
    assert "roof_type/facade_is_gable" in issue.message
    assert "n’inventez aucune métrique" in issue.message
