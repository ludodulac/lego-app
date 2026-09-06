from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "frontend" / "scene-handoff-contract-audit-v44.js"
RUNTIME = ROOT / "frontend" / "scene-benchmark-runtime.js"


def test_scene_handoff_teaches_non_metric_platform_structure_contract() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    assert 'platform_structure_observations' in text
    assert '"vertical_post"' in text
    assert '"diagonal_brace"' in text
    assert '"guardrail"' in text
    assert 'Use Platform.supports only for SupportPost geometry' in text
    assert 'instead of fabricating metric supports' in text
    assert 'preserve a guardrail observation rather than inventing Platform.edges' in text


def test_scene_handoff_requires_joint_spatial_structural_reasoning() -> None:
    text = AUDIT.read_text(encoding="utf-8")
    assert 'occupied 3D space' in text
    assert 'stair start/end and direction of ascent' in text
    assert 'massive landing/secondary volume footprint' in text
    assert 'contact versus gap' in text
    assert 'above/below' in text
    assert 'overlap in plan' in text
    assert 'protrusion/overhang' in text
    assert 'physically bears or receives' in text
    assert 'not LEGO-ready merely because it validates syntactically' in text


def test_strict_audit_is_loaded_before_photo_handoff_generation() -> None:
    text = RUNTIME.read_text(encoding="utf-8")
    audit_pos = text.index("scene-handoff-contract-audit-v44.js")
    photo_pos = text.index("scene-handoff-photo-evidence.js")
    assert audit_pos < photo_pos
