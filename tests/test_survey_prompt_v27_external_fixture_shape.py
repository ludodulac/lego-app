import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey


def test_fresh_external_fixture_is_architectural_survey_shape_valid() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    survey=ArchitecturalSurvey.model_validate(payload)
    assert survey.schema_version=="0.1"
    assert survey.canonical_frame.x_direction=="front_view_left_to_right"
