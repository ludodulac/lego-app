import json
from pathlib import Path

def test_fresh_external_fixture_weathering_policy_is_preserved():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert payload['representation_policy']['reproduce_weathering'] is True
