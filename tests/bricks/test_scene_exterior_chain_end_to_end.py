from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.55}


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "exterior-chain",
        "name": "Resolved stair landing terrace chain",
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
        "platforms": [
            {
                "id": "concrete_landing",
                "host_volume_id": "volume_main",
                "position": {"x": -1.2, "y": 5.0, "z": 2.4},
                "width": 1.2,
                "depth": 1.5,
                "thickness": 0.25,
                "material": "concrete",
                "source": SOURCE,
                "evidence": [{"photo_index": 1, "observation": "walkable concrete landing visibly meets wall"}],
            },
            {
                "id": "timber_terrace",
                "host_volume_id": "volume_main",
                "position": {"x": -2.8, "y": 5.0, "z": 2.4},
                "width": 1.6,
                "depth": 1.5,
                "thickness": 0.2,
                "material": "timber",
                "deck_board_direction": "y",
                "supports": [{
                    "id": "terrace_post",
                    "position": {"x": -2.6, "y": 5.2, "z": 0},
                    "width": 0.15,
                    "depth": 0.15,
                    "height": 2.4,
                    "source": SOURCE,
                }],
                "source": SOURCE,
                "evidence": [{"photo_index": 2, "observation": "timber deck visibly joins concrete landing"}],
            },
        ],
        "stairs": [{
            "id": "exterior_stair",
            "start": {"x": -0.6, "y": 3.5, "z": 0},
            "end": {"x": -0.6, "y": 5.0, "z": 2.4},
            "width": 1.0,
            "material": "concrete",
            "left_edge": "solid_parapet",
            "right_edge": "unknown",
            "source": SOURCE,
            "evidence": [{"photo_index": 2, "observation": "stair visibly ends on landing"}],
        }],
        "relations": [
            {
                "id": "stair_to_landing",
                "kind": "connects_to",
                "subject_id": "exterior_stair",
                "object_id": "concrete_landing",
                "certainty": "certain",
                "geometry_status": "resolved",
                "statement": "The stair visibly ends on the concrete landing.",
                "evidence": [{"photo_index": 2, "observation": "top tread meets landing"}],
            },
            {
                "id": "landing_to_terrace",
                "kind": "connects_to",
                "subject_id": "concrete_landing",
                "object_id": "timber_terrace",
                "certainty": "certain",
                "geometry_status": "resolved",
                "statement": "The concrete landing and timber terrace share a visible edge.",
                "evidence": [{"photo_index": 2, "observation": "material transition is continuous"}],
            },
            {
                "id": "landing_to_building",
                "kind": "connects_to",
                "subject_id": "concrete_landing",
                "object_id": "left_boundary",
                "certainty": "certain",
                "geometry_status": "resolved",
                "semantic_anchor_volume_id": "volume_main",
                "statement": "The landing visibly meets the building wall.",
                "evidence": [{"photo_index": 1, "observation": "landing slab edge meets wall"}],
            },
        ],
        "appearance": {
            "walls": {"color": "off_white"},
            "roof": {"color": "dark_gray"},
            "frames": {"color": "dark_brown"},
        },
    })


def test_resolved_exterior_chain_survives_to_final_brick_model():
    bundle = run_m0_pipeline_scene(_scene(), front_width_studs=48)
    ids = [part.placement_id for part in bundle.brick_model.parts]
    assert any(value.startswith("scene-stair:exterior_stair:tread:") for value in ids)
    assert any(value.startswith("scene-platform:concrete_landing:deck:") for value in ids)
    assert any(value.startswith("scene-platform:timber_terrace:board:") for value in ids)
    assert any("scene-platform:timber_terrace:support" in value for value in ids)


def test_temporary_buildingmodel_losses_are_not_final_export_losses():
    bundle = run_m0_pipeline_scene(_scene(), front_width_studs=48)
    codes = {issue.code for issue in bundle.fidelity_issues}
    assert "platform_not_supported" not in codes
    assert "stair_not_supported" not in codes
