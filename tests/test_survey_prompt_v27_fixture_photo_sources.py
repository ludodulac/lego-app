import json
from pathlib import Path

def test_fresh_external_fixture_photo_sources_are_user_provided():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert all(p['source']['kind']=='user_provided' for p in payload['photos'])
