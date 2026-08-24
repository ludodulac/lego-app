import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_roof_semantic_validation_is_pure():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); s=ArchitecturalSurvey.model_validate(p); before=s.model_dump(mode='json'); validate_survey_semantics(s); assert s.model_dump(mode='json')==before
