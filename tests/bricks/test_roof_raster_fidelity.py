from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.roof import _footprint, generate_spatial_gable_roof
from brickhouse.bricks.roof_raster_fidelity import select_gable_roof_raster
from brickhouse.building.models import BuildingModel
from brickhouse.geometry import generate_building_geometry
from brickhouse.pipeline import run_m0_pipeline_model


def _building(*, width: float, depth: float) -> BuildingModel:
    return BuildingModel.model_validate(
        {
            "schema_version": "0.1",
            "id": "roof-raster",
            "name": "Generic roof raster fixture",
            "building_type": "test",
            "units": "m",
            "volumes": [
                {
                    "id": "main",
                    "shape": "rectangular_prism",
                    "position": {"x": 0, "y": 0, "z": 0},
                    "width": width,
                    "depth": depth,
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
                    "overhang": 0.0,
                    "ridge_direction": "depth",
                    "pitch_degrees": 18.0,
                    "source": {"kind": "inferred", "confidence": 0.9},
                }
            ],
            "appearance": {},
            "metadata": {"created_from": "synthetic"},
        }
    )


def _geometry_shell(building: BuildingModel, front_width_studs: int):
    geometry = generate_building_geometry(building)
    shell = generate_building_brick_shell(geometry, front_width_studs)
    return geometry, shell


def _selection(building: BuildingModel, front_width_studs: int):
    geometry, shell = _geometry_shell(building, front_width_studs)
    return select_gable_roof_raster(geometry, shell)


def test_exact_gable_raster_reports_no_representation_adjustment() -> None:
    selection = _selection(_building(width=8.5, depth=7.0), 17)

    assert selection.slope_family_id == "18"
    assert selection.wall_span_studs == 17
    assert selection.selected_span_studs == 17
    assert selection.wall_line_length_studs == 14
    assert selection.selected_line_length_studs == 14
    assert selection.span_adjustment_studs == 0
    assert selection.line_adjustment_studs == 0
    assert selection.geometry_changed is False


def test_quantized_gable_raster_exposes_both_lego_only_overhangs() -> None:
    selection = _selection(_building(width=8.0, depth=6.5), 16)

    assert selection.slope_family_id == "18"
    assert selection.wall_span_studs == 16
    assert selection.selected_span_studs == 17
    assert selection.wall_line_length_studs == 13
    assert selection.selected_line_length_studs == 14
    assert selection.span_adjustment_studs == 1
    assert selection.line_adjustment_studs == 1
    assert selection.geometry_changed is True


def test_selection_matches_the_actual_generated_roof_footprint() -> None:
    building = _building(width=8.0, depth=6.5)
    geometry, shell = _geometry_shell(building, 16)
    selection = select_gable_roof_raster(geometry, shell)
    roof = generate_spatial_gable_roof(geometry, shell)

    cells = set().union(*(_footprint(placement) for placement in roof.placements))
    assert min(x for x, _ in cells) == 0
    assert max(x for x, _ in cells) + 1 == selection.selected_span_studs
    assert min(y for _, y in cells) == 0
    assert max(y for _, y in cells) + 1 == selection.selected_line_length_studs


def test_raster_selection_is_deterministic_and_does_not_mutate_building() -> None:
    building = _building(width=8.0, depth=6.5)
    before = building.model_dump(mode="json")

    first = _selection(building, 16)
    second = _selection(building, 16)

    assert first == second
    assert building.model_dump(mode="json") == before


def test_pipeline_surfaces_quantized_roof_raster_as_representation_only_fidelity() -> None:
    building = _building(width=8.0, depth=6.5)
    before = building.model_dump(mode="json")

    bundle = run_m0_pipeline_model(building, front_width_studs=16)
    issues = {issue.code: issue for issue in bundle.fidelity_issues}

    assert issues["lego_roof_eave_span_adjustment"].object_id == "roof"
    assert issues["lego_roof_eave_span_adjustment"].severity == "info"
    assert issues["lego_roof_gable_line_adjustment"].object_id == "roof"
    assert issues["lego_roof_gable_line_adjustment"].severity == "info"
    assert building.model_dump(mode="json") == before


def test_pipeline_emits_no_roof_raster_adjustment_when_catalog_tiles_exactly() -> None:
    bundle = run_m0_pipeline_model(
        _building(width=8.5, depth=7.0),
        front_width_studs=17,
    )
    codes = {issue.code for issue in bundle.fidelity_issues}

    assert "lego_roof_eave_span_adjustment" not in codes
    assert "lego_roof_gable_line_adjustment" not in codes
