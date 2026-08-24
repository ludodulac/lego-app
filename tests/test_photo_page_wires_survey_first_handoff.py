from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def test_photo_page_loads_survey_first_handoff_instead_of_legacy_bundle_handoff() -> None:
    html = (FRONTEND / "photo.html").read_text(encoding="utf-8")
    assert 'src="./brickhouse-survey-package.js?v=pdf-handoff-0.3"' in html
    assert 'src="./brickhouse-single-package.js"' not in html


def test_survey_first_handoff_exposes_expected_version() -> None:
    source = (FRONTEND / "brickhouse-survey-package.js").read_text(encoding="utf-8")
    assert "pdf-handoff-0.3" in source
    assert "brickhouse-survey-result.json" in source
