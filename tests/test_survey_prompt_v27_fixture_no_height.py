import json
from pathlib import Path

def test_fresh_external_fixture_does_not_fabricate_roof_height():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert 'height' not in payload['observations'][0].get('attributes',{})
