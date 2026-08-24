import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_roof_type_counts_as_shape_even_if_ridge_direction_is_also_present():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['attributes']={'roof_type':'gable','ridge_direction':'front_to_rear'}; p['observations'][0]['attribute_certainty']={'roof_type':'plausible','ridge_direction':'unproven'}; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
