import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_fresh_external_fixture_reproduces_exact_roof_issue():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    survey=ArchitecturalSurvey.model_validate(payload)
    assert [(i.code,i.observation_id,i.severity) for i in validate_survey_semantics(survey)]==[('multiview_roof_missing_shape_hypothesis','roof_main_01','error')]
