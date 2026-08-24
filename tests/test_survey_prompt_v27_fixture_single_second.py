import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_single_view_second_roof_without_shape_does_not_add_blocker():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); second={**p['observations'][0],'id':'roof_second','evidence':[p['observations'][0]['evidence'][0]]}; p['observations'].append(second); s=ArchitecturalSurvey.model_validate(p); assert [i.observation_id for i in validate_survey_semantics(s)]==['roof_main_01']
