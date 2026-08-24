import json
from pathlib import Path

def test_fresh_external_fixture_temporary_objects_policy_is_false():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert payload['representation_policy']['reproduce_temporary_objects'] is False
