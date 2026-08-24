import json
from pathlib import Path

def test_fresh_external_fixture_contains_no_scene_or_lego_payload():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert 'scene' not in payload
    assert 'brick_model' not in payload
