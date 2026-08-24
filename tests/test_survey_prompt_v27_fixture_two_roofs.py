import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_two_multiview_roofs_missing_shape_report_two_object_specific_issues():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); second={**p['observations'][0],'id':'roof_second'}; p['observations'].append(second); s=ArchitecturalSurvey.model_validate(p); issues=validate_survey_semantics(s); assert [i.observation_id for i in issues]==['roof_main_01','roof_second']
