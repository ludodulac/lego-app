import json
from pathlib import Path

def test_fresh_external_fixture_is_minimal_two_view_reproduction():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert len(payload['photos'])==2
