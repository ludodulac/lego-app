import pytest

from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.5}


def _scene(platform_x=-1.2):
    return {
        "schema_version": "0.2",
        "id": "semantic-anchor",
        "name": "Semantic boundary metric resolution",
        "units": "m",
        "volumes": [{
            "id": "volume_main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 1}},
            "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 7, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "platforms": [{
            "id": "landing",
            "host_volume_id": "volume_main",
            "position": {"x": platform_x, "y": 4, "z": 2.4},
            "width": 1.2,
            "depth": 1.5,
            "thickness": 0.2,
            "material": "concrete",
            "source": SOURCE,
        }],
        "relations": [{
            "id": "landing_to_left_boundary",
            "kind": "connects_to",
            "subject_id": "landing",
            "object_id": "left_boundary",
            "certainty": "certain",
            "geometry_status": "resolved",
            "semantic_anchor_volume_id": "volume_main",
            "statement": "The landing visibly touches the building boundary.",
            "evidence": [{"photo_index": 1, "observation": "landing edge meets wall"}],
        }],
        "appearance": {"walls": {"color": "off_white"}},
    }


def test_semantic_boundary_id_is_preserved_while_metric_contact_maps_to_volume():
    scene = ArchitecturalScene.model_validate(_scene())
    relation = scene.relations[0]
    assert relation.object_id == "left_boundary"
    assert relation.geometry_status == "resolved"
    assert relation.semantic_anchor_volume_id == "volume_main"


def test_resolved_semantic_boundary_requires_real_metric_contact():
    with pytest.raises(ValueError, match="not reflected by metric contact"):
        ArchitecturalScene.model_validate(_scene(platform_x=-1.5))


def test_unresolved_relation_cannot_claim_metric_anchor():
    payload = _scene()
    payload["relations"][0]["geometry_status"] = "unresolved"
    with pytest.raises(ValueError, match="cannot claim a semantic_anchor_volume_id"):
        ArchitecturalScene.model_validate(payload)
