import json
from pathlib import Path
from brickhouse.survey import ArchitecturalSurvey

def test_missing_roof_maps_stay_empty():
    p=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text())
    r=ArchitecturalSurvey.model_validate(p).observations[0]
    assert r.attributes=={} and r.attribute_certainty=={}
