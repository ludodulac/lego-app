import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_only_missing_shape_roof_is_reported_when_other_roof_has_hypothesis():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); second={**p['observations'][0],'id':'roof_second','attributes':{'roof_type':'gable'},'attribute_certainty':{'roof_type':'plausible'}}; p['observations'].append(second); s=ArchitecturalSurvey.model_validate(p); assert [i.observation_id for i in validate_survey_semantics(s)]==['roof_main_01']
