import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_false_gable_hypothesis_counts_when_other_roof_attributes_exist():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['attributes']={'facade_is_gable':False,'material':'tile'}; p['observations'][0]['attribute_certainty']={'facade_is_gable':'plausible','material':'plausible'}; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
