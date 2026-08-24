import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_explicit_roof_relationship_without_attribute_certainty_is_not_silent_loss():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['attributes']={'facade_roof_relationship':'gable_end'}; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
