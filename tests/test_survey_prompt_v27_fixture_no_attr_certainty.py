import json
from pathlib import Path

def test_fresh_external_fixture_roof_has_no_attribute_certainty_map():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert payload['observations'][0].get('attribute_certainty') is None
