import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_multiview_platform_alongside_missing_roof_does_not_add_extra_issue():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'].append({'id':'p','kind':'platform','certainty':'certain','statement':'platform','evidence':p['observations'][0]['evidence']}); s=ArchitecturalSurvey.model_validate(p); assert [i.code for i in validate_survey_semantics(s)]==['multiview_roof_missing_shape_hypothesis']
