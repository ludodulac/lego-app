import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_roof_blocker_remains_with_three_distinct_evidence_views():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); p['photos'].append({'photo_index':3,'facade':'left','description':'left','source':{'kind':'user_provided','confidence':1},'image_left_maps_to_facade_offset':'low'}); p['observations'][0]['evidence'].append({'photo_index':3,'observation':'roof edge'}); s=ArchitecturalSurvey.model_validate(p); assert [i.code for i in validate_survey_semantics(s)]==['multiview_roof_missing_shape_hypothesis']
