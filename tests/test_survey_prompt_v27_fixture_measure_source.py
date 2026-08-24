import json
from pathlib import Path

def test_fresh_external_fixture_width_source_is_user_provided():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert payload['known_measurements'][0]['source']['kind']=='user_provided'
