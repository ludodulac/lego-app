import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_roof_shape_information_rule_is_independent_of_evidence_order():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['evidence'].reverse(); s=ArchitecturalSurvey.model_validate(p); assert [i.code for i in validate_survey_semantics(s)]==['multiview_roof_missing_shape_hypothesis']
