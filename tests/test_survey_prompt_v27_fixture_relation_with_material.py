import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_roof_relationship_counts_when_other_attributes_exist():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['attributes']={'facade_roof_relationship':'gable_end','material':'tile'}; p['observations'][0]['attribute_certainty']={'facade_roof_relationship':'plausible','material':'plausible'}; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
