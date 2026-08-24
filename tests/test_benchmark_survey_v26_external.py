import json
from pathlib import Path

from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

FIXTURE = Path(__file__).parent / "fixtures" / "benchmark_survey_v26_external.json"


def test_fresh_v26_external_survey_is_shape_valid_but_semantically_blocks_roof_information_loss() -> None:
    survey = ArchitecturalSurvey.model_validate(json.loads(FIXTURE.read_text(encoding="utf-8")))
    codes = {issue.code for issue in validate_survey_semantics(survey)}
    assert codes == {"multiview_roof_missing_shape_hypothesis"}
