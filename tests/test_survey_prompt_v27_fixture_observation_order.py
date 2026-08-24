import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_roof_shape_information_rule_finds_roof_after_other_observation():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'].insert(0,{'id':'p','kind':'platform','certainty':'certain','statement':'p','evidence':[p['observations'][0]['evidence'][0]]}); s=ArchitecturalSurvey.model_validate(p); assert [i.observation_id for i in validate_survey_semantics(s)]==['roof_main_01']
