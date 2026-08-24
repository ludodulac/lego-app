import json
from pathlib import Path

def test_fresh_external_fixture_has_right_roof_view():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert any(p['facade']=='right' for p in payload['photos'])
