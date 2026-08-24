import json
from pathlib import Path

def test_fresh_external_fixture_statement_keeps_metric_unknowns_explicit():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert 'forme métrique' in payload['observations'][0]['statement']
    assert 'pente exacte' in payload['observations'][0]['statement']
