import json
from pathlib import Path

import pytest

from brickhouse.scene import ArchitecturalScene


FIXTURE = Path("tests/fixtures/brickhouse_scene_current.json")


def _fixture_data():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_existing_scene_remains_valid_without_wall_profiles():
    scene = ArchitecturalScene.model_validate_json(FIXTURE.read_text(encoding="utf-8"))
    assert scene.wall_profile_observations == []


def test_five_photo_scene_can_record_recessed_openings_without_inventing_wall_thickness():
    data = _fixture_data()
    data["wall_profile_observations"] = [
        {
            "id": "right_wall_profile",
            "volume_id": "volume_main",
            "facade": "right",
            "openings_recessed": True,
            "wall_thickness": {
                "value": None,
                "source": {"kind": "observed", "confidence": 0.82},
                "evidence": [
                    {
                        "photo_index": 2,
                        "observation": "The side opening exposes a visibly deep reveal, proving non-zero wall depth without calibrating a metric thickness."
                    }
                ]
            },
            "source": {"kind": "observed", "confidence": 0.82},
            "evidence": [
                {
                    "photo_index": 2,
                    "observation": "The window plane is visibly behind the exterior wall face."
                }
            ]
        },
        {
            "id": "left_wall_profile",
            "volume_id": "volume_main",
            "facade": "left",
            "openings_recessed": True,
            "wall_thickness": {
                "value": None,
                "source": {"kind": "observed", "confidence": 0.84},
                "evidence": [
                    {
                        "photo_index": 4,
                        "observation": "The upper opening and glazed door show substantial masonry returns from the exterior face to the frame plane."
                    }
                ]
            },
            "source": {"kind": "observed", "confidence": 0.84},
            "evidence": [
                {
                    "photo_index": 3,
                    "observation": "The side view shows the frame set behind the facade plane."
                },
                {
                    "photo_index": 4,
                    "observation": "The closer view independently confirms the same recessed opening geometry."
                }
            ]
        }
    ]

    scene = ArchitecturalScene.model_validate(data)
    assert len(scene.wall_profile_observations) == 2
    assert all(item.openings_recessed is True for item in scene.wall_profile_observations)
    assert all(item.wall_thickness.value is None for item in scene.wall_profile_observations)


def test_wall_profile_rejects_impossible_or_ambiguous_contracts():
    data = _fixture_data()
    data["wall_profile_observations"] = [
        {
            "id": "profile",
            "volume_id": "volume_main",
            "facade": "front",
            "openings_recessed": True,
            "wall_thickness": {"value": 0.2, "source": {"kind": "inferred", "confidence": 0.5}},
            "reveal_depth": {"value": 0.3, "source": {"kind": "inferred", "confidence": 0.5}},
            "source": {"kind": "inferred", "confidence": 0.5}
        }
    ]
    with pytest.raises(ValueError, match="cannot exceed wall_thickness"):
        ArchitecturalScene.model_validate(data)


def test_wall_profile_scope_must_reference_one_real_facade_once():
    data = _fixture_data()
    profile = {
        "id": "profile-a",
        "volume_id": "missing",
        "facade": "right",
        "openings_recessed": True,
        "source": {"kind": "observed", "confidence": 0.8}
    }
    data["wall_profile_observations"] = [profile]
    with pytest.raises(ValueError, match="references unknown volume"):
        ArchitecturalScene.model_validate(data)

    profile["volume_id"] = "volume_main"
    data["wall_profile_observations"] = [profile, {**profile, "id": "profile-b"}]
    with pytest.raises(ValueError, match="at most one wall profile observation"):
        ArchitecturalScene.model_validate(data)
