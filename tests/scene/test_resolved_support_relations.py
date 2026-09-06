import json
from pathlib import Path

import pytest

from brickhouse.scene import ArchitecturalScene

SOURCE = {"kind": "inferred", "confidence": 0.7}
ROOT = Path(__file__).resolve().parents[2]
REAL_HOUSE_SCENE = ROOT / "tests" / "fixtures" / "real_house_5_scene_candidate.json"


def _payload(*, platform_x=0.5, platform_z=2.0, geometry_status="resolved") -> dict:
    return {
        "schema_version": "0.2",
        "id": "support-relation-scene",
        "name": "Resolved structural support",
        "units": "m",
        "volumes": [{
            "id": "bearing-volume",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 3, "source": SOURCE},
            "depth": {"value": 3, "source": SOURCE},
            "height": {"value": 2, "source": SOURCE},
            "floors": 1,
            "source": SOURCE,
        }],
        "platforms": [{
            "id": "landing",
            "host_volume_id": "bearing-volume",
            "position": {"x": platform_x, "y": 0.5, "z": platform_z},
            "width": 2,
            "depth": 2,
            "thickness": 0.2,
            "material": "masonry",
            "source": SOURCE,
        }],
        "relations": [{
            "id": "volume-supports-landing",
            "kind": "supports",
            "subject_id": "bearing-volume",
            "object_id": "landing",
            "certainty": "certain",
            "geometry_status": geometry_status,
            "statement": "bearing volume supports landing",
            "evidence": [{"photo_index": 1, "observation": "landing is visibly on top of volume"}],
        }],
        "appearance": {"walls": {"color": "off_white"}},
    }


def test_resolved_volume_supports_platform_when_bearing_geometry_matches():
    scene = ArchitecturalScene.model_validate(_payload())
    assert scene.relations[0].geometry_status == "resolved"


def test_resolved_support_rejects_horizontal_disjointness():
    with pytest.raises(ValueError, match="supports is not reflected by metric bearing"):
        ArchitecturalScene.model_validate(_payload(platform_x=4.0))


def test_resolved_support_rejects_wrong_vertical_bearing_level():
    with pytest.raises(ValueError, match="supports is not reflected by metric bearing"):
        ArchitecturalScene.model_validate(_payload(platform_z=2.5))


def test_unresolved_support_preserves_relation_without_claiming_metric_bearing():
    payload = _payload(platform_x=4.0, platform_z=2.5, geometry_status="unresolved")
    scene = ArchitecturalScene.model_validate(payload)
    assert scene.relations[0].geometry_status == "unresolved"


def test_incomplete_support_volume_does_not_fabricate_a_contradiction():
    payload = _payload()
    payload["volumes"][0]["height"]["value"] = None
    # A complete host volume keeps the landing architecturally connected while the
    # separate bearing volume remains metrically unresolved.
    payload["volumes"].append({
        "id": "host",
        "position": {"x": 2.5, "y": 0, "z": 0},
        "width": {"value": 2, "source": SOURCE},
        "depth": {"value": 3, "source": SOURCE},
        "height": {"value": 2, "source": SOURCE},
        "floors": 1,
        "source": SOURCE,
    })
    payload["platforms"][0]["host_volume_id"] = "host"
    payload["platforms"][0]["position"]["x"] = 2.0
    scene = ArchitecturalScene.model_validate(payload)
    assert scene.volumes[0].height.value is None


def test_real_house_massive_landing_support_relation_has_metric_bearing():
    payload = json.loads(REAL_HOUSE_SCENE.read_text(encoding="utf-8"))
    scene = ArchitecturalScene.model_validate(payload)
    relation = next(item for item in scene.relations if item.id == "relation-volume-supports-platform")
    assert relation.geometry_status == "resolved"
    assert relation.subject_id == "volume-exterior-1"
    assert relation.object_id == "platform-massive-1"
