import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_adding_certain_gable_attribute_is_semantically_valid_when_explicit():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['attributes']={'roof_type':'gable'}; p['observations'][0]['attribute_certainty']={'roof_type':'certain'}; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
