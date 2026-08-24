from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.7}


def _scene(*, platform_material="timber", stair_material="concrete", left_edge="solid_parapet", right_edge="none") -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "structured-exterior",
        "name": "Structured exterior",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": SOURCE},
            "depth": {"value": 8, "source": SOURCE},
            "height": {"value": 6, "source": SOURCE},
            "floors": 2,
            "source": SOURCE,
        }],
        "platforms": [{
            "id": "deck",
            "position": {"x": -2, "y": 4, "z": 2},
            "width": 2,
            "depth": 3,
            "thickness": 0.6,
            "supports": [],
            "material": platform_material,
            "edge_treatment": "none",
            "source": SOURCE,
            "evidence": [{"photo_index": 1, "observation": "plateforme extérieure"}],
        }],
        "stairs": [{
            "id": "stair",
            "start": {"x": -1, "y": 2, "z": 0},
            "end": {"x": -1, "y": 4.5, "z": 2},
            "width": 1,
            "material": stair_material,
            "left_edge": left_edge,
            "right_edge": right_edge,
            "source": SOURCE,
            "evidence": [{"photo_index": 1, "observation": "volée extérieure"}],
        }],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
    })


def test_timber_platform_uses_one_deck_course_without_text_material_hint() -> None:
    bundle = run_m0_pipeline_scene(_scene(), front_width_studs=48)
    deck_parts = [part for part in bundle.brick_model.parts if part.placement_id.startswith("scene-platform:deck:board:")]
    assert deck_parts
    assert len({part.z_plates for part in deck_parts}) == 1


def test_concrete_stair_emits_only_the_explicit_solid_sidewall() -> None:
    bundle = run_m0_pipeline_scene(_scene(), front_width_studs=48)
    sidewalls = [part for part in bundle.brick_model.parts if part.placement_id.startswith("scene-stair:stair:left-parapet:")]
    assert sidewalls
    # One parapet means one sidewall cell per height level, not symmetric walls on both sides.
    xy = {(part.x_studs, part.y_studs) for part in sidewalls}
    assert len(xy) > 1
    # There must be fewer sidewall cells than if both sides were mirrored at every stair step.
    tread_xy = {(part.x_studs, part.y_studs) for part in bundle.brick_model.parts if part.placement_id.startswith("scene-stair:stair:tread:")}
    assert len(xy) < len(tread_xy)
    assert not any(part.placement_id.startswith("scene-stair:stair:right-parapet:") for part in bundle.brick_model.parts)


def test_legacy_scene_without_structured_fields_still_validates() -> None:
    raw = _scene().model_dump(mode="json")
    for platform in raw["platforms"]:
        platform.pop("material", None)
        platform.pop("edge_treatment", None)
    for stair in raw["stairs"]:
        stair.pop("material", None)
        stair.pop("left_edge", None)
        stair.pop("right_edge", None)
    assert ArchitecturalScene.model_validate(raw).id == "structured-exterior"
