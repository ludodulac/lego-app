import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_front_gable_rake_shape_information_is_valid():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); r=p['observations'][0]; r['facade']='front'; r['attributes']={'facade_roof_relationship':'gable_end','roof_edge_type':'rake'}; r['attribute_certainty']={'facade_roof_relationship':'plausible','roof_edge_type':'plausible'}; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
