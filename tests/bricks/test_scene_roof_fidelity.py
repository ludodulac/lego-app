from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


def _scene(pitch):
    return ArchitecturalScene.model_validate({
        "schema_version":"0.2","id":"roof-fidelity","name":"Roof fidelity","units":"m",
        "volumes":[{
            "id":"main","position":{"x":0,"y":0,"z":0},
            "width":{"value":10,"source":{"kind":"user_provided","confidence":1}},
            "depth":{"value":10,"source":{"kind":"inferred","confidence":.7}},
            "height":{"value":6,"source":{"kind":"inferred","confidence":.7}},
            "floors":2,"source":{"kind":"inferred","confidence":.7},
        }],
        "roofs":[{
            "id":"roof","volume_id":"main","type":"gable","overhang":.2,
            "ridge_direction":"depth","pitch_degrees":pitch,
            "source":{"kind":"inferred","confidence":.7},
        }],
        "appearance":{"walls":{"color":"off_white"},"roof":{"color":"dark_gray"},"frames":{"color":"dark_brown"}},
    })


def test_22_degree_scene_uses_low_pitch_parts_and_reports_four_degree_approximation():
    bundle=run_m0_pipeline_scene(_scene(22),front_width_studs=48)
    slope_ids={part.part_id for part in bundle.brick_model.parts if part.category=="roof_tile"}
    assert "BRICK_SLOPED_18_4X2" in slope_ids
    issues=[issue for issue in bundle.fidelity_issues if issue.code=="roof_pitch_quantized"]
    assert len(issues)==1
    assert issues[0].object_id=="roof"
    assert issues[0].severity=="info"
    assert "22°" in issues[0].message
    assert "18°" in issues[0].message


def test_exact_supported_pitch_does_not_claim_quantization_loss():
    bundle=run_m0_pipeline_scene(_scene(18),front_width_studs=48)
    assert not any(issue.code=="roof_pitch_quantized" for issue in bundle.fidelity_issues)
