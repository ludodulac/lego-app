import json
from pathlib import Path


def test_fresh_external_fixture_uses_backend_canonical_frame() -> None:
    payload=json.loads((Path(__file__).parent/"fixtures"/"benchmark_survey_v26_external.json").read_text(encoding="utf-8"))
    assert payload["canonical_frame"]=={"front_facade":"front","x_direction":"front_view_left_to_right","y_direction":"front_to_rear","z_direction":"bottom_to_top"}
