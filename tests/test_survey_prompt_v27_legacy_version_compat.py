from pathlib import Path


def test_v27_history_keeps_v26_marker_for_traceability() -> None:
    source = (Path(__file__).resolve().parents[1] / "frontend" / "brickhouse-survey-prompt.txt").read_text(encoding="utf-8")
    assert "v2.6" in source
