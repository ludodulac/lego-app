from pathlib import Path
import subprocess

from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.scene_cli import load_architectural_scene


SCENE = Path("tests/fixtures/brickhouse_scene_current.json")


def test_five_photo_export_carries_scale_recommendation_separate_from_grid_report():
    scene = load_architectural_scene(SCENE)
    bundle = run_partial_scene_pipeline(scene, front_width_studs=48)

    assert bundle.metadata.discretization_quality
    recommendation = bundle.metadata.scale_recommendation
    assert recommendation is not None
    assert recommendation.preferred_front_width_studs == 48
    assert 42 <= recommendation.recommended_front_width_studs <= 54
    assert recommendation.recommended.score_m <= recommendation.baseline.score_m


def test_viewer_has_visible_precision_card_and_valid_modules():
    html = Path("frontend/viewer.html").read_text(encoding="utf-8")
    assert 'id="precision-card"' in html
    assert 'id="precision-summary"' in html
    assert 'viewer-precision.js' in html

    for path in ("frontend/precision-summary.js", "frontend/viewer-precision.js"):
        result = subprocess.run(["node", "--check", path], capture_output=True, text=True)
        assert result.returncode == 0, result.stderr


def test_precision_copy_keeps_grid_rounding_distinct_from_photo_uncertainty():
    js = Path("frontend/viewer-precision.js").read_text(encoding="utf-8")
    assert "arrondi LEGO" in js
    assert "incertitude des photos" in js
    assert "réduirait le score d'erreur de grille" in js
