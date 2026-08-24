from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_photo_page_loads_survey_first_handoff_instead_of_legacy_bundle_handoff() -> None:
    html = (FRONTEND / "photo.html").read_text(encoding="utf-8")
    assert 'src="./brickhouse-survey-package.js?v=pdf-handoff-0.3"' in html
    assert 'src="./brickhouse-single-package.js"' not in html


def test_survey_first_handoff_entry_point_forwards_to_expected_version() -> None:
    loader = (FRONTEND / "brickhouse-survey-package.js").read_text(encoding="utf-8")
    implementation = (FRONTEND / "brickhouse-survey-package-v04.js").read_text(encoding="utf-8")
    assert "brickhouse-survey-package-v04.js?v=pdf-handoff-0.4" in loader
    assert "pdf-handoff-0.4" in implementation
    assert "brickhouse-survey-result.json" in implementation
