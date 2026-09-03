import pytest

from brickhouse.bricks.brick_model import generate_brick_model
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.roof import _footprint, generate_spatial_gable_roof, validate_roof_support
from brickhouse.bricks.roof_raster_fidelity import select_gable_roof_raster
from brickhouse.bricks.spatial import generate_spatial_brick_shell
from brickhouse.building.models import BuildingModel, RidgeDirection
from brickhouse.geometry import generate_building_geometry


def _building(
    direction: RidgeDirection,
    *,
    overhang: float,
    pitch_degrees: float = 33.0,
) -> BuildingModel:
    return BuildingModel.model_validate(
        {
            "schema_version": "0.1",
            "id": "roof-overhang",
            "name": "Generic declared roof overhang fixture",
            "building_type": "test",
            "units": "m",
            "volumes": [
                {
                    "id": "main",
                    "shape": "rectangular_prism",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "width": 8.0,
                    "depth": 6.0,
                    "height": 4.0,
                    "floors": 1,
                    "source": {"kind": "inferred", "confidence": 0.9},
                }
            ],
            "openings": [],
            "roofs": [
                {
                    "id": "roof",
                    "volume_id": "main",
                    "type": "gable",
                    "overhang": overhang,
                    "ridge_direction": direction.value,
                    "pitch_degrees": pitch_degrees,
                    "source": {"kind": "inferred", "confidence": 0.9},
                }
            ],
            "appearance": {},
            "metadata": {"created_from": "synthetic"},
        }
    )


def _roof_cells(roof):
    return set().union(*(_footprint(placement) for placement in roof.placements))


@pytest.mark.parametrize("direction", [RidgeDirection.DEPTH, RidgeDirection.WIDTH])
def test_declared_overhang_survives_both_gable_roof_axes(direction):
    building = _building(direction, overhang=0.5)
    before = building.model_dump(mode="json")
    geometry = generate_building_geometry(building)
    shell = generate_building_brick_shell(geometry, 16)

    roof = generate_spatial_gable_roof(geometry, shell)
    cells = _roof_cells(roof)
    run_values = [x if direction is RidgeDirection.DEPTH else y for x, y in cells]
    line_values = [y if direction is RidgeDirection.DEPTH else x for x, y in cells]
    wall_run = shell.reference_width_studs if direction is RidgeDirection.DEPTH else next(
        wall.grid.width_studs for wall in shell.walls if wall.facade.value == "right"
    )
    wall_line = next(
        wall.grid.width_studs for wall in shell.walls if wall.facade.value == "right"
    ) if direction is RidgeDirection.DEPTH else shell.reference_width_studs

    # 16 front studs over 8m means 2 studs/m: the declared 0.5m overhang
    # must survive as at least one stud on every architectural roof edge.
    assert min(run_values) == -1
    assert max(run_values) + 1 >= wall_run + 1
    assert min(line_values) == -1
    assert max(line_values) + 1 >= wall_line + 1
    assert all(
        placement.part_id.startswith("BRICK_SLOPED_33_")
        for placement in roof.placements
        if placement.side in {"negative", "positive"}
    )
    validate_roof_support(roof, shell)
    assert building.model_dump(mode="json") == before


@pytest.mark.parametrize("direction", [RidgeDirection.DEPTH, RidgeDirection.WIDTH])
def test_brick_model_reserves_non_negative_canvas_for_symmetric_roof_overhang(direction):
    building = _building(direction, overhang=0.5)
    geometry = generate_building_geometry(building)
    shell = generate_building_brick_shell(geometry, 16)
    roof = generate_spatial_gable_roof(geometry, shell)
    model = generate_brick_model(generate_spatial_brick_shell(shell), roof)

    assert min(part.x_studs for part in model.parts) >= 0
    assert min(part.y_studs for part in model.parts) >= 0
    wall_parts = [part for part in model.parts if part.component == "wall"]
    assert min(part.x_studs for part in wall_parts) == 1
    assert min(part.y_studs for part in wall_parts) == 1
    # Architectural dimensions stay stable; only the representation canvas grows.
    assert model.width_studs == shell.reference_width_studs
    assert model.canvas_width_studs is not None
    assert model.canvas_depth_studs is not None
    assert model.canvas_width_studs >= model.origin_x_studs + model.width_studs
    assert model.canvas_depth_studs >= model.origin_y_studs + model.depth_studs
    assert model.canvas_width_studs >= shell.reference_width_studs + 2


def test_declared_overhang_is_not_reported_as_lego_only_quantization():
    building = _building(RidgeDirection.DEPTH, overhang=0.5)
    geometry = generate_building_geometry(building)
    shell = generate_building_brick_shell(geometry, 16)

    selection = select_gable_roof_raster(geometry, shell)

    assert selection.wall_span_studs == 16
    assert selection.architectural_span_studs == 18
    assert selection.declared_span_overhang_studs == 2
    assert selection.wall_line_length_studs == 12
    assert selection.architectural_line_length_studs == 14
    assert selection.declared_line_overhang_studs == 2
    assert selection.selected_span_studs >= selection.architectural_span_studs
    assert selection.selected_line_length_studs >= selection.architectural_line_length_studs
    assert selection.span_adjustment_studs == (
        selection.selected_span_studs - selection.architectural_span_studs
    )
    assert selection.line_adjustment_studs == (
        selection.selected_line_length_studs - selection.architectural_line_length_studs
    )


def test_zero_overhang_keeps_historical_zero_origin_layout():
    building = _building(RidgeDirection.DEPTH, overhang=0.0)
    geometry = generate_building_geometry(building)
    shell = generate_building_brick_shell(geometry, 16)
    roof = generate_spatial_gable_roof(geometry, shell)
    cells = _roof_cells(roof)
    model = generate_brick_model(generate_spatial_brick_shell(shell), roof)
    selection = select_gable_roof_raster(geometry, shell)

    assert min(x for x, _ in cells) == 0
    assert min(y for _, y in cells) == 0
    wall_parts = [part for part in model.parts if part.component == "wall"]
    assert min(part.x_studs for part in wall_parts) == 0
    assert min(part.y_studs for part in wall_parts) == 0
    assert model.origin_x_studs == 0
    assert model.origin_y_studs == 0
    assert selection.architectural_span_studs == selection.wall_span_studs
    assert selection.architectural_line_length_studs == selection.wall_line_length_studs


def test_declared_overhang_is_not_silently_shrunk_when_eave_support_is_impossible():
    building = _building(RidgeDirection.DEPTH, overhang=1.5)
    geometry = generate_building_geometry(building)
    shell = generate_building_brick_shell(geometry, 16)

    with pytest.raises(ValueError, match="preserve declared overhang"):
        generate_spatial_gable_roof(geometry, shell)
