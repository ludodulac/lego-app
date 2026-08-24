import json
from pathlib import Path

def test_fresh_external_fixture_keeps_photo_offset_mapping():
    payload=json.loads((Path(__file__).parent/'fixtures'/'benchmark_survey_v26_external.json').read_text(encoding='utf-8'))
    assert [p['image_left_maps_to_facade_offset'] for p in payload['photos']]==['low','high']
