import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_duplicate_first_roof_evidence_does_not_trigger_multiview_blocker():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); first=p['observations'][0]['evidence'][0]; p['observations'][0]['evidence']=[first,{**first,'observation':'second note same photo'}]; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
