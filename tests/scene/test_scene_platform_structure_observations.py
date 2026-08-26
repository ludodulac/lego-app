import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from brickhouse.scene import ArchitecturalScene


def _brickhouse_payload() -> dict:
    return json.loads(Path("tests/fixtures/brickhouse_scene_current.json").read_text(encoding="utf-8"))


def test_brickhouse_scene_can_preserve_observed_deck_structure_without_coordinates() -> None:
    payload = _brickhouse_payload()
    payload["platform_structure_observations"] = [
        {
            "id": "timber-deck-visible-posts",
            "platform_id": "timber_deck",
            "kind": "vertical_post",
            "statement": "Vertical timber supports are directly visible below the deck; exact count and coordinates remain unresolved.",
            "count": None,
            "source": {"kind": "observed", "confidence": 0.98},
            "evidence": [
                {"photo_index": 3, "observation": "Vertical timber support is visible below the raised deck."},
                {"photo_index": 4, "observation": "A deck support is visible again beneath the outer edge."},
            ],
        },
        {
            "id": "timber-deck-visible-bracing",
            "platform_id": "timber_deck",
            "kind": "diagonal_brace",
            "statement": "Diagonal timber bracing is directly visible below the deck; exact member count and endpoints remain unresolved.",
            "count": None,
            "source": {"kind": "observed", "confidence": 0.96},
            "evidence": [{"photo_index": 3, "observation": "Diagonal brace members are visible beneath the deck."}],
        },
    ]

    scene = ArchitecturalScene.model_validate(payload)
    assert [item.kind.value for item in scene.platform_structure_observations] == ["vertical_post", "diagonal_brace"]
    assert all(item.count is None for item in scene.platform_structure_observations)
    assert scene.platforms[0].supports == []


def test_platform_structure_observation_must_reference_a_real_platform() -> None:
    payload = _brickhouse_payload()
    payload["platform_structure_observations"] = [
        {
            "id": "orphan-support",
            "platform_id": "missing-platform",
            "kind": "vertical_post",
            "statement": "Visible support with unresolved metric geometry.",
            "source": {"kind": "observed", "confidence": 0.9},
            "evidence": [{"photo_index": 3, "observation": "Visible support."}],
        }
    ]
    with pytest.raises(ValidationError, match="references unknown platform"):
        ArchitecturalScene.model_validate(payload)
