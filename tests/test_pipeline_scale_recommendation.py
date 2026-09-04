from pathlib import Path

from brickhouse.building.validation import load_building_model
from brickhouse.pipeline import run_m0_pipeline_model, run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


BUILDING_FIXTURE = Path("docs/examples/building-model-simple-house.json")
SCENE_FIXTURE = Path("docs/examples/architectural-scene-rich-exterior.json")


def _scale_sensitive_building():
    building = load_building_model(BUILDING_FIXTURE)
    opening = building.openings[0].model_copy(update={
        "offset_horizontal": 1.4,
        "offset_vertical": 1.2,
        "width": 1.4,
        "height": 1.2,
    })
    return building.model_copy(update={"openings": [opening]})


def test_pipeline_recommends_nearby_scale_without_changing_requested_build_width():
    bundle = run_m0_pipeline_model(_scale_sensitive_building(), front_width_studs=48)
    recommendation = bundle.metadata.scale_recommendation

    assert bundle.brick_model.width_studs == 48
    assert recommendation is not None
    assert recommendation.preferred_front_width_studs == 48
    assert recommendation.recommended_front_width_studs != 48
    assert abs(recommendation.recommended_front_width_studs - 48) <= recommendation.search_radius_studs
    assert recommendation.recommended.score_m < recommendation.baseline.score_m
    assert recommendation.improvement_fraction > 0.5


def test_scene_enrichment_preserves_base_scale_recommendation_metadata():
    scene = ArchitecturalScene.model_validate_json(SCENE_FIXTURE.read_text(encoding="utf-8"))
    bundle = run_m0_pipeline_scene(scene, front_width_studs=48)

    assert bundle.metadata.scale_recommendation is not None
    assert bundle.metadata.scale_recommendation.preferred_front_width_studs == 48
    assert bundle.metadata.discretization_quality
