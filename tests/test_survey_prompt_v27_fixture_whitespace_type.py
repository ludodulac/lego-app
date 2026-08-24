import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_whitespace_roof_type_does_not_count_as_shape_hypothesis():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['attributes']={'roof_type':'   '}; s=ArchitecturalSurvey.model_validate(p); assert 'multiview_roof_missing_shape_hypothesis' in {i.code for i in validate_survey_semantics(s)}
