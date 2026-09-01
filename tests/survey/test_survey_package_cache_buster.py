from pathlib import Path


PHOTO_PAGE = Path("frontend/photo.html")
PACKAGE_ENTRY = Path("frontend/brickhouse-survey-package.js")


def test_photo_page_cache_buster_matches_active_survey_package_layer():
    page = PHOTO_PAGE.read_text(encoding="utf-8")
    entry = PACKAGE_ENTRY.read_text(encoding="utf-8")
    assert "brickhouse-survey-package-v07.js" in entry
    assert "pdf-handoff-0.7-coverage-audit" in entry
    assert "scene-handoff-source-lock.js" in entry
    assert 'brickhouse-survey-package.js?v=pdf-handoff-0.8-scene-source-lock' in page
    assert 'brickhouse-survey-package.js?v=pdf-handoff-0.7-coverage-preflight' not in page
