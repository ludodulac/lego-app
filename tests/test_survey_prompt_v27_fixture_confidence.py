import json
from pathlib import Path

def test_fresh_external_fixture_user_inputs_have_full_confidence():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert all(p['source']['confidence']==1.0 for p in payload['photos'])
    assert payload['known_measurements'][0]['source']['confidence']==1.0
