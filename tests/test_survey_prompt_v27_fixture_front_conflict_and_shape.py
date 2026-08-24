import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_front_gable_eave_conflict_remains_only_issue_when_shape_info_exists():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); r=p['observations'][0]; r['facade']='front'; r['attributes']={'facade_roof_relationship':'gable_end','roof_edge_type':'eave_across_facade'}; s=ArchitecturalSurvey.model_validate(p); assert [i.code for i in validate_survey_semantics(s)]==['gable_eave_terminology_conflict']
