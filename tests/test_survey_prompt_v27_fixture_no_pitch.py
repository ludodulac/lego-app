import json
from pathlib import Path

def test_fresh_external_fixture_does_not_fabricate_roof_pitch():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    roof=payload['observations'][0]
    assert 'pitch_degrees' not in roof.get('attributes',{})
