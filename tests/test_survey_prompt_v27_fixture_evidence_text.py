import json
from pathlib import Path

def test_fresh_external_fixture_evidence_is_roof_edge_based():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert all('rive' in e['observation'] for e in payload['observations'][0]['evidence'])
