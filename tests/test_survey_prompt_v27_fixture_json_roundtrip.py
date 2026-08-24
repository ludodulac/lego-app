import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_roof_blocker_survives_model_roundtrip():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); s=ArchitecturalSurvey.model_validate(p); s2=ArchitecturalSurvey.model_validate(s.model_dump(mode='json')); assert [i.code for i in validate_survey_semantics(s2)]==['multiview_roof_missing_shape_hypothesis']
