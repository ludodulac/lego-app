from typing import get_args

from brickhouse.scene.readiness import ReadinessSource


def test_readiness_sources_are_architectural_behavior_categories():
    assert set(get_args(ReadinessSource)) == {"survey", "projection", "required_input", "m0"}
