import json
from pathlib import Path

def test_fresh_external_fixture_contains_no_unrelated_platforms():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert all(o['kind']!='platform' for o in payload['observations'])
