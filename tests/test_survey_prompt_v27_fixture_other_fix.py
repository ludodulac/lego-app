import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_adding_plausible_other_roof_hypothesis_clears_fresh_blocker():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['attributes']={'roof_type':'other'}; p['observations'][0]['attribute_certainty']={'roof_type':'plausible'}; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
