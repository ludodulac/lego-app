import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_multiple_consistent_roof_shape_clues_are_valid():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); r=p['observations'][0]; r['attributes']={'roof_type':'gable','facade_is_gable':True,'roof_edge_type':'rake'}; r['attribute_certainty']={'roof_type':'plausible','facade_is_gable':'plausible','roof_edge_type':'plausible'}; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
