from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_chimneys import augment_brick_model_with_scene_chimneys
from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


FIXTURE = Path("tests/fixtures/architectural_scene_real_house_v02.json")


def test_scene_pipeline_renders_metric_chimney_into_brick_model_bom_and_assembly() -> None:
    scene = ArchitecturalScene.model_validate_json(FIXTURE.read_text(encoding="utf-8"))

    bundle = run_m0_pipeline_scene(scene, front_width_studs=48)

    chimney_parts = [
        part
        for part in bundle.brick_model.parts
        if part.placement_id.startswith("scene-chimney:chimney_main_01:")
    ]
    assert chimney_parts
    assert all(part.part_id == "BRICK_1X1" for part in chimney_parts)
    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan is not None
    assert bundle.assembly_plan.total_steps > 0
    assert "chimney_not_supported" not in {issue.code for issue in bundle.fidelity_issues}


def _minimal_chimney_scene() -> ArchitecturalScene:
    source = {"kind": "inferred", "confidence": 1.0}
    prop = lambda value: {"value": value, "source": source, "evidence": []}
    return ArchitecturalScene.model_validate(
        {
            "schema_version": "0.2",
            "id": "chimney-clearance",
            "name": "chimney clearance",
            "units": "m",
            "volumes": [
                {
                    "id": "main",
                    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "width": prop(10.0),
                    "depth": prop(10.0),
                    "height": prop(5.0),
                    "floors": 1,
                    "source": source,
                    "evidence": [],
                }
            ],
            "chimneys": [
                {
                    "id": "c",
                    "position": {"x": 0.25, "y": 0.25, "z": 0.0},
                    "width": 0.25,
                    "depth": 0.25,
                    "height": 1.0,
                    "source": source,
                    "evidence": [],
                }
            ],
            "appearance": {},
        }
    )


def test_metric_chimney_carves_whole_intersecting_roof_element() -> None:
    model = BrickModel(
        building_id="b",
        volume_id="main",
        width_studs=40,
        depth_studs=40,
        height_plates=6,
        parts=[
            BrickModelPart(
                placement_id="roof-hit",
                part_id="BRICK_SLOPED_45_2X4",
                category="roof_tile",
                component="roof",
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                roof_side="negative",
            ),
            BrickModelPart(
                placement_id="roof-clear",
                part_id="BRICK_SLOPED_45_2X4",
                category="roof_tile",
                component="roof",
                x_studs=3,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                roof_side="negative",
            ),
        ],
    )

    augmented = augment_brick_model_with_scene_chimneys(
        model,
        _minimal_chimney_scene(),
        front_width_studs=40,
    )

    ids = {part.placement_id for part in augmented.parts}
    assert "roof-hit" not in ids
    assert "roof-clear" in ids
    chimney_parts = [
        part for part in augmented.parts if part.placement_id.startswith("scene-chimney:c:")
    ]
    assert chimney_parts
    assert {(part.x_studs, part.y_studs) for part in chimney_parts} == {(1, 1)}


def test_chimney_clearance_does_not_move_architectural_grid() -> None:
    model = BrickModel(
        building_id="b",
        volume_id="main",
        width_studs=40,
        depth_studs=40,
        height_plates=3,
        parts=[
            BrickModelPart(
                placement_id="roof-clear",
                part_id="BRICK_SLOPED_45_2X4",
                category="roof_tile",
                component="roof",
                x_studs=3,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                roof_side="negative",
            )
        ],
    )

    augmented = augment_brick_model_with_scene_chimneys(
        model,
        _minimal_chimney_scene(),
        front_width_studs=40,
    )
    assert augmented.width_studs == 40
    assert augmented.depth_studs == 40
