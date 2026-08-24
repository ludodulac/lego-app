import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey, validate_survey_semantics

def test_front_width_anchor_alone_never_counts_as_roof_shape_information():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text()); s=ArchitecturalSurvey.model_validate(p); assert s.known_measurements and [i.code for i in validate_survey_semantics(s)]==['multiview_roof_missing_shape_hypothesis']
