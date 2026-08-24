import json
from pathlib import Path

def test_fresh_external_fixture_has_canonical_front_photo():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert any(p['facade']=='front' for p in payload['photos'])
