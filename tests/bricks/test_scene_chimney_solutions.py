from brickhouse.building.models import Facade
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.scene_chimney_solutions import select_scene_chimney_footprints
from brickhouse.bricks.scene_chimneys import augment_brick_model_with_scene_chimneys
from brickhouse.pipeline import run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


SOURCE = {"kind": "inferred", "confidence": 0.9}


def _scene(*, chimney_width=0.30, chimney_depth=0.55):
    prop = lambda value: {"value": value, "source": SOURCE, "evidence": []}
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "generic-chimney-footprint",
        "name": "Generic chimney footprint",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0.0, "y": 0.0, "z": 0.0},
            "width": prop(8.0),
            "depth": prop(6.0),
            "height": prop(4.0),
            "floors": 1,
            "source": SOURCE,
        }],
        "chimneys": [{
            "id": "chimney-a",
            "position": {"x": 2.0, "y": 2.0, "z": 3.0},
            "width": chimney_width,
            "depth": chimney_depth,
            "height": 1.0,
            "source": SOURCE,
        }],
        "appearance": {},
    })


def _base_model():
    return BrickModel(
        building_id="generic",
        volume_id="main",
        width_studs=32,
        depth_studs=24,
        height_plates=48,
        parts=[
            BrickModelPart(
                placement_id="base-wall-cell",
                part_id="BRICK_1X1",
                category="brick",
                component="wall",
                x_studs=0,
                y_studs=0,
                z_plates=0,
                rotation_quarter_turns=0,
                facade=Facade.FRONT,
            )
        ],
    )


def test_chimney_footprint_selection_avoids_independent_outward_rounding():
    scene = _scene()
    solution = select_scene_chimney_footprints(scene, front_width_studs=32)[0]

    # 4 studs/m gives a metric target of 1.2 x 2.2 studs. Independent ceil
    # would produce 2 x 3; the proportional solution is the much closer 1 x 2.
    assert solution.target_width_studs == 1.2
    assert solution.target_depth_studs == 2.2
    assert (solution.width_studs, solution.depth_studs) == (1, 2)
    assert solution.aspect_ratio_error < 0.1


def test_chimney_footprint_selection_preserves_axis_orientation():
    scene = _scene(chimney_width=0.55, chimney_depth=0.30)
    solution = select_scene_chimney_footprints(scene, front_width_studs=32)[0]
    assert (solution.width_studs, solution.depth_studs) == (2, 1)


def test_renderer_uses_selected_footprint_without_mutating_scene():
    scene = _scene()
    before = scene.model_dump(mode="json", by_alias=True)

    result = augment_brick_model_with_scene_chimneys(
        _base_model(),
        scene,
        front_width_studs=32,
    )

    parts = [part for part in result.parts if part.placement_id.startswith("scene-chimney:chimney-a:")]
    assert parts
    footprint = {(part.x_studs, part.y_studs) for part in parts}
    assert len(footprint) == 2
    assert len({x for x, _ in footprint}) == 1
    assert len({y for _, y in footprint}) == 2
    assert scene.model_dump(mode="json", by_alias=True) == before


def test_scene_pipeline_surfaces_chimney_footprint_adjustment():
    scene = _scene()
    before = scene.model_dump(mode="json", by_alias=True)

    bundle = run_m0_pipeline_scene(scene, front_width_studs=32)

    issues = [
        issue for issue in bundle.fidelity_issues
        if issue.code == "lego_chimney_footprint_adjustment"
    ]
    assert len(issues) == 1
    assert issues[0].object_id == "chimney-a"
    assert "1x2 studs" in issues[0].message
    assert scene.model_dump(mode="json", by_alias=True) == before


def test_exact_integer_chimney_footprint_needs_no_adjustment_issue():
    scene = _scene(chimney_width=0.50, chimney_depth=0.25)
    solution = select_scene_chimney_footprints(scene, front_width_studs=32)[0]
    assert (solution.target_width_studs, solution.target_depth_studs) == (2.0, 1.0)
    assert (solution.width_studs, solution.depth_studs) == (2, 1)
    assert not solution.geometry_changed

    bundle = run_m0_pipeline_scene(scene, front_width_studs=32)
    assert "lego_chimney_footprint_adjustment" not in {
        issue.code for issue in bundle.fidelity_issues
    }
