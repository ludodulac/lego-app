from pathlib import Path


def test_ai_start_here_indexes_current_continuity_sources():
    text = Path("AI_START_HERE.md").read_text(encoding="utf-8")
    assert "PROGRESSION.md" in text
    assert "docs/CURRENT_PROJECT_STATE.md" in text
    assert "docs/ARCHITECTURE.md" in text
    assert "docs/DECISIONS.md" in text
    assert "Lis `AI_START_HERE.md`, vérifie l’état réel de `main` et reprends le projet." in text


def test_legacy_handoff_points_to_current_entrypoint():
    text = Path("HANDOFF.md").read_text(encoding="utf-8")
    assert "AI_START_HERE.md" in text
    assert "docs/HANDOFF_HISTORY_2026-08-23.md" in text
    assert "docs/CURRENT_PROJECT_STATE.md" in text
