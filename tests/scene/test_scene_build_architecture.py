from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


def _scene() -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "scene-rich-build",
        "name": "Rich scene build",
        "units": "m",
        "volumes": [{
            "id": "volume_main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 1.0}},
            "depth": {"value": 8, "source": {"kind": "inferred", "confidence": 0.5}},
            "height": {"value": 6, "source": {"kind": "inferred", "confidence": 0.5}},
            "floors": 2,
            "source": {"kind": "inferred", "confidence": 0.6},
        }],
        "platforms": [{
            "id": "left_platform",
            "position": {"x": -2, "y": 4, "z": 2},
            "width": 2,
            "depth": 3,
            "thickness": 0.25,
            "supports": [],
            "source": {"kind": "inferred", "confidence": 0.5},
        }],
        "stairs": [{
            "id": "left_stair",
            "start": {"x": -1, "y": 2, "z": 0},
            "end": {"x": -1, "y": 4.5, "z": 2},
            "width": 1,
            "source": {"kind": "inferred", "confidence": 0.5},
        }],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
    })


def test_scene_build_keeps_platform_and_stair_parts() -> None:
    bundle = run_m0_pipeline_scene(_scene(), front_width_studs=48)
    ids = {part.placement_id for part in bundle.brick_model.parts}
    assert any(value.startswith("scene-platform:left_platform:") for value in ids)
    assert any(value.startswith("scene-stair:left_stair:") for value in ids)
    assert all(part.x_studs >= 0 and part.y_studs >= 0 and part.z_plates >= 0 for part in bundle.brick_model.parts)
    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan is not None
    assert bundle.assembly_plan.total_parts == len(bundle.brick_model.parts)
