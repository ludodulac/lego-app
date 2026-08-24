import json
from pathlib import Path

def test_fresh_external_fixture_roof_is_not_encoded_as_volume():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert payload['observations'][0]['kind']!='volume'
