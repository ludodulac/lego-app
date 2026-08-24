import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_nonfront_gable_eave_words_do_not_trigger_front_terminology_guard():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); r=p['observations'][0]; r['facade']='right'; r['attributes']={'facade_roof_relationship':'gable_end','roof_edge_type':'eave_across_facade'}; s=ArchitecturalSurvey.model_validate(p); assert validate_survey_semantics(s)==[]
