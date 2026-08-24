import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_removing_second_roof_evidence_view_removes_multiview_blocker():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['evidence']=p['observations'][0]['evidence'][:1]; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
