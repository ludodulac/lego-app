import json
from pathlib import Path

def test_fresh_external_fixture_detail_policy_is_true():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert payload['representation_policy']['preserve_architectural_details'] is True
