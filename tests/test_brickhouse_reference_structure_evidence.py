import json
from pathlib import Path


def test_reference_preview_bundles_independent_five_photo_summary() -> None:
    payload = json.loads(Path("frontend/brickhouse-independent-analysis.json").read_text(encoding="utf-8"))
    expected = payload["regression_expectations"]
    assert expected["deck_vertical_posts_observed"] is True
    assert expected["deck_diagonal_bracing_observed"] is True
    assert expected["photo_5_proves_distinct_rear_facade"] is False


def test_reference_preview_attaches_non_metric_deck_structure_observation() -> None:
    source = Path("frontend/brickhouse-reference-preview.js").read_text(encoding="utf-8")
    assert "brickhouse-independent-analysis.json" in source
    assert "platform_structure_observations" in source
    assert "vertical_posts" in source
    assert "diagonal_bracing" in source
    assert "exact_count_known: false" in source
    assert "exact_coordinates_known: false" in source
    assert "BoxGeometry" not in source
    assert "Mesh(" not in source
