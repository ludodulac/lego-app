import json
from pathlib import Path

def test_fresh_external_fixture_needs_no_boundary_observation_for_roof_regression():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert all(o['kind']!='building_boundary' for o in payload['observations'])
