import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_roof_type_counts_as_shape_even_if_pitch_is_also_present():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['attributes']={'roof_type':'gable','pitch_degrees':35}; p['observations'][0]['attribute_certainty']={'roof_type':'plausible','pitch_degrees':'unproven'}; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
