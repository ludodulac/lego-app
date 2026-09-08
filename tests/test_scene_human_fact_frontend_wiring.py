from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "frontend" / "scene-human-fact-handoff.js"
SOURCE_LOCK = ROOT / "frontend" / "scene-handoff-source-lock.js"
ACTIVE_IMPORT = ROOT / "frontend" / "external-bundle-import.js"
PHOTO_PAGE = ROOT / "frontend" / "photo.html"


def test_human_fact_client_keeps_accepted_survey_storage_separate() -> None:
    source = CLIENT.read_text(encoding="utf-8")

    assert "brickhouse.pendingHumanFactSceneHandoff" in source
    assert "/api/v1/prepare-human-fact-scene-handoff" in source
    assert "human_facts: humanFacts" in source
    assert "scene_input_survey" in source
    assert "storage.setItem(HUMAN_FACT_SCENE_HANDOFF_KEY" in source
    assert "brickhouse.pendingArchitecturalSurvey" not in source


def test_scene_source_lock_prefers_only_matching_validated_derived_handoff() -> None:
    source = SOURCE_LOCK.read_text(encoding="utf-8")

    assert "readHumanFactSceneHandoff" in source
    assert "effectiveSceneInput" in source
    assert "handoff?.source_survey_id === acceptedSurvey.id" in source
    assert "handoff?.scene_input_survey?.schema_version === '0.1'" in source
    assert "survey: handoff.scene_input_survey" in source
    assert "humanFacts: handoff.human_facts" in source
    assert "human_facts: humanFacts" in source
    assert "stair_topology" in source


def test_source_lock_does_not_turn_human_facts_into_measurements() -> None:
    source = SOURCE_LOCK.read_text(encoding="utf-8")

    assert "known_measurements: survey.known_measurements ?? []" in source
    assert "faits sémantiques user_provided" in source
    assert "ne deviennent jamais des known_measurements" in source


def test_active_photo_page_loads_source_lock_before_scene_handoff_generation() -> None:
    page = PHOTO_PAGE.read_text(encoding="utf-8")
    active_import = ACTIVE_IMPORT.read_text(encoding="utf-8")
    source_lock = SOURCE_LOCK.read_text(encoding="utf-8")

    assert './external-bundle-import.js' in page
    assert './scene-handoff-photo-evidence.js' in page
    assert page.index('./external-bundle-import.js') < page.index('./scene-handoff-photo-evidence.js')
    assert "import './scene-handoff-source-lock.js';" in active_import

    ordered_audits = [
        "scene-handoff-contract-audit-v44.js",
        "scene-handoff-stage-lock-v45.js",
        "scene-handoff-output-frame-v46.js",
        "scene-handoff-ownership-audit-v47.js",
        "scene-handoff-scale-audit-v48.js",
    ]
    positions = [source_lock.index(name) for name in ordered_audits]
    assert positions == sorted(positions)
