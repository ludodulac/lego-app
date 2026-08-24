import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_explicit_roof_type_without_attribute_certainty_is_not_silent_shape_loss():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['attributes']={'roof_type':'gable'}; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
