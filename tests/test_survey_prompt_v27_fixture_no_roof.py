import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_survey_without_roof_observation_is_not_blocked_by_roof_rule():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations']=[]; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
