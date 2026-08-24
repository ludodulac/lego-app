import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_adding_unproven_facade_gable_flag_preserves_information():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['attributes']={'facade_is_gable':True}; p['observations'][0]['attribute_certainty']={'facade_is_gable':'unproven'}; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
