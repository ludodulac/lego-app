from pathlib import Path


INDEX_HTML = Path("frontend/index.html").read_text(encoding="utf-8")
APP_JS = Path("frontend/app.js").read_text(encoding="utf-8")


def test_photo_shell_is_the_primary_boldungo_entry_without_removing_manual_compatibility():
    photo_link = '<a class="choice" href="./photo.html">'
    manual_link = '<a class="choice" href="./configurator.html">'
    assert photo_link in INDEX_HTML
    assert manual_link in INDEX_HTML
    assert INDEX_HTML.index(photo_link) < INDEX_HTML.index(manual_link)
    assert "Parcours principal" in INDEX_HTML
    assert "Survey" in INDEX_HTML
    assert "Scene" in INDEX_HTML
    assert 'class="choice disabled" href="./photo.html"' not in INDEX_HTML


def test_home_status_does_not_claim_photo_workflow_is_unavailable_when_external_handoff_exists():
    assert "Handoff externe disponible" in INDEX_HTML
    assert "Handoff externe disponible" in APP_JS
    assert "En attente d’activation" not in APP_JS
