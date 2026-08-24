from brickhouse.building.models import BuildingModel
from brickhouse.vision.compatibility import assess_m0_compatibility


def test_window_fidelity_limit_is_explicit_before_build() -> None:
    building = BuildingModel.model_validate({
        "schema_version": "0.1",
        "id": "window-warning",
        "name": "Window warning",
        "building_type": "house",
        "units": "m",
        "volumes": [{"id": "v", "shape": "rectangular_prism", "position": {"x": 0, "y": 0, "z": 0}, "width": 10, "depth": 8, "height": 6, "floors": 2, "source": {"kind": "user_provided", "confidence": 1}}],
        "openings": [{"id": "w", "type": "window", "volume_id": "v", "facade": "front", "offset_horizontal": 2, "offset_vertical": 2, "width": 1.4, "height": 1.5, "source": {"kind": "inferred", "confidence": 0.7}, "window_style": "paired", "has_sill": True, "has_decorative_surround": True}],
        "roofs": [{"id": "r", "volume_id": "v", "type": "gable", "overhang": 0.3, "ridge_direction": "depth", "pitch_degrees": 25, "source": {"kind": "inferred", "confidence": 0.7}}],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
        "metadata": {"created_from": "photo_analysis"},
    })
    result = assess_m0_compatibility(building)
    assert result.buildable is True
    assert any("cadre + vitrage" in warning for warning in result.warnings)
    assert any("sans inventer" in warning for warning in result.warnings)
