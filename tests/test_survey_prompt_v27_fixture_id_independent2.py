import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_roof_shape_information_rule_is_independent_of_roof_id_name():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['id']='r1'; s=ArchitecturalSurvey.model_validate(p); issue=validate_survey_semantics(s)[0]; assert issue.code=='multiview_roof_missing_shape_hypothesis' and issue.observation_id=='r1'
