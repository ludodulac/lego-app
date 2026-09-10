from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_checkpoint_bridge_does_not_feed_its_own_mutation_observer():
    source = (ROOT / 'frontend' / 'photo-checkpoint-flow.js').read_text(encoding='utf-8')
    assert 'function setText(node, message)' in source
    assert "node.textContent !== message" in source
    observer = source.split('new MutationObserver(sync).observe', 1)[1]
    assert 'characterData: true' not in observer


def test_fresh_real_house_benchmark_clears_resumable_workflow_state():
    source = (ROOT / 'frontend' / 'real-house-benchmark-loader.js').read_text(encoding='utf-8')
    assert 'resetFreshBenchmarkWorkflow();' in source
    assert "requestedStage()) return" in source
    for key in (
        'brickhouse.pendingArchitecturalSurvey',
        'brickhouse.knownFrontWidthM',
        'brickhouse.lastRejectedArchitecturalScene',
        'brickhouse.lastSceneValidationError',
    ):
        assert key in source
