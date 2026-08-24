import json
from pathlib import Path

def test_fresh_external_fixture_has_no_generated_default_roof_source():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    roof=payload['observations'][0]
    assert roof.get('source') is None
