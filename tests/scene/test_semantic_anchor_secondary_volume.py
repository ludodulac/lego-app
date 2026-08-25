import pytest
from pydantic import ValidationError

from brickhouse.scene import ArchitecturalScene

SOURCE = {"kind": "inferred", "confidence": 0.5}


def _scene(lower_x: float) -> dict:
    return {
        "schema_version": "0.2",
        "id": "scene",
        "name": "secondary volume semantic anchor",
        "units": "m",
        "volumes": [
            {
                "id": "volume_main",
                "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                "width": {"value": 10.0, "source": SOURCE},
                "depth": {"value": 11.8, "source": SOURCE},
                "height": {"value": 8.4, "source": SOURCE},
                "floors": 3,
                "source": SOURCE,
            },
            {
                "id": "obs-left-lower-volume",
                "position": {"x": lower_x, "y": 6.6, "z": 0.0},
                "width": {"value": 3.0, "source": SOURCE},
                "depth": {"value": 3.4, "source": SOURCE},
                "height": {"value": 3.0, "source": SOURCE},
                "floors": 1,
                "source": SOURCE,
            },
        ],
        "relations": [
            {
                "id": "rel-left-lower-volume-to-building",
                "kind": "connects_to",
                "subject_id": "obs-left-lower-volume",
                "object_id": "building_boundary",
                "certainty": "certain",
                "geometry_status": "resolved",
                "semantic_anchor_volume_id": "volume_main",
                "statement": "The lower volume visibly connects to the main building envelope.",
            }
        ],
        "appearance": {},
    }


def test_resolved_semantic_anchor_accepts_touching_secondary_volume() -> None:
    scene = ArchitecturalScene.model_validate(_scene(-3.0))
    relation = scene.relations[0]
    assert relation.geometry_status == "resolved"
    assert relation.semantic_anchor_volume_id == "volume_main"


def test_resolved_semantic_anchor_rejects_detached_secondary_volume() -> None:
    with pytest.raises(ValidationError, match="not reflected by metric contact"):
        ArchitecturalScene.model_validate(_scene(-4.0))
