import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_multiview_unproven_roof_still_cannot_drop_all_shape_information():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['certainty']='unproven'; s=ArchitecturalSurvey.model_validate(p); assert [i.code for i in validate_survey_semantics(s)]==['multiview_roof_missing_shape_hypothesis']
