import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_boolean_true_facade_is_gable_counts_as_shape_information():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['attributes']={'facade_is_gable':True}; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
