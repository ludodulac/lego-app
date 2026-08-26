from pathlib import Path

import pytest

from brickhouse.partial_scene_pipeline import AUTO_SCALE_MIN_IMPROVEMENT, run_partial_scene_pipeline
from brickhouse.scene_cli import load_architectural_scene, write_scene_export


SCENE = Path("tests/fixtures/brickhouse_scene_current.json")


def test_photo_build_applies_recommended_scale_only_when_gain_is_meaningful():
    scene = load_architectural_scene(SCENE)
    fixed = run_partial_scene_pipeline(scene, front_width_studs=48, optimize_scale=False)
    optimized = run_partial_scene_pipeline(scene, front_width_studs=48, optimize_scale=True)

    recommendation = optimized.metadata.scale_recommendation
    assert recommendation is not None
    assert fixed.brick_model.width_studs == 48
    if recommendation.improvement_fraction >= AUTO_SCALE_MIN_IMPROVEMENT:
        assert optimized.brick_model.width_studs == recommendation.recommended_front_width_studs
        assert recommendation.recommended.score_m < recommendation.baseline.score_m
    else:
        assert optimized.brick_model.width_studs == 48


def test_scene_cli_keeps_scale_optimization_explicit(tmp_path: Path):
    fixed = write_scene_export(
        SCENE,
        tmp_path / "fixed.json",
        front_width_studs=48,
        allow_partial=True,
        optimize_scale=False,
    )
    assert fixed.brick_model.width_studs == 48

    with pytest.raises(ValueError, match="requires allow_partial"):
        write_scene_export(
            SCENE,
            tmp_path / "invalid.json",
            front_width_studs=48,
            allow_partial=False,
            optimize_scale=True,
        )
