import json
from pathlib import Path

def test_fresh_external_fixture_does_not_fabricate_ridge_direction():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert 'ridge_direction' not in payload['observations'][0].get('attributes',{})
