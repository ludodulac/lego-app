import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_ridge_direction_alone_does_not_substitute_for_qualitative_roof_shape():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['observations'][0]['attributes']={'ridge_direction':'front_to_rear'}; s=ArchitecturalSurvey.model_validate(p); assert [i.code for i in validate_survey_semantics(s)]==['multiview_roof_missing_shape_hypothesis']
