from brickhouse.pipeline_probe import probe_pipeline
from brickhouse.scene import ArchitecturalScene, project_scene_to_building
from brickhouse.survey import ArchitecturalSurvey


USER = {"kind": "user_provided", "confidence": 1.0}
INFERRED = {"kind": "inferred", "confidence": 0.55}


def _survey() -> ArchitecturalSurvey:
    return ArchitecturalSurvey.model_validate({
        "schema_version": "0.1",
        "id": "generic-shed-survey",
        "name": "Generic shed survey",
        "photos": [{"photo_index": 1, "facade": "front", "description": "canonical front", "source": USER}],
        "known_measurements": [{"kind": "front_width", "value": 10, "units": "m", "source": USER}],
        "observations": [
            {"id": "building_main", "kind": "building_boundary", "certainty": "certain", "statement": "Main building exists.", "evidence": [{"photo_index": 1, "observation": "front envelope visible"}]},
            {"id": "roof_main", "kind": "roof", "certainty": "certain", "statement": "A roof certainly exists; shed form is only plausible.", "evidence": [{"photo_index": 1, "observation": "roof edge visible"}], "attributes": {"roof_type": "shed"}, "attribute_certainty": {"roof_type": "plausible"}},
        ],
    })


def _scene(*, direction=None, pitch=None) -> ArchitecturalScene:
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "generic-shed-scene",
        "name": "Generic shed scene",
        "units": "m",
        "volumes": [{"id": "volume_main", "position": {"x": 0, "y": 0, "z": 0}, "width": {"value": 10, "source": USER}, "depth": {"value": 8, "source": INFERRED}, "height": {"value": 6, "source": INFERRED}, "floors": 2, "source": INFERRED}],
        "roofs": [{"id": "roof_main", "volume_id": "volume_main", "type": "shed", "overhang": 0.2, "ridge_direction": None, "down_slope_direction": direction, "pitch_degrees": pitch, "source": INFERRED, "evidence": [{"photo_index": 1, "observation": "mono-pitch hypothesis"}]}],
        "appearance": {},
    })


def test_probe_reports_incomplete_shed_geometry_at_scene_projection() -> None:
    report = probe_pipeline(_survey(), _scene())
    assert report["first_blocking_stage"] == "scene_to_building_projection"
    assert "shed_geometry_incomplete" in report["projection_issue_codes"]
    assert [item["field"] for item in report["required_inputs"]] == ["down_slope_direction", "pitch_degrees"]
    assert report["m0_error"] is None


def test_direction_without_numeric_pitch_remains_honestly_blocked() -> None:
    report = probe_pipeline(_survey(), _scene(direction="rear"))
    assert report["first_blocking_stage"] == "scene_to_building_projection"
    assert "shed_geometry_incomplete" in report["projection_issue_codes"]
    assert report["required_inputs"] == [{"object_id": "roof_main", "field": "pitch_degrees", "kind": "exact_metric", "reason": "shed_construction_requires_exact_pitch"}]


def test_complete_shed_contract_projects_without_false_roof_conversion() -> None:
    scene = _scene(direction="rear", pitch=12.0)
    projection = project_scene_to_building(scene)
    assert projection.building is not None
    assert not projection.blocked
    assert projection.building.roofs[0].type.value == "shed"
    assert projection.building.roofs[0].down_slope_direction.value == "rear"
    assert projection.building.roofs[0].pitch_degrees == 12.0


def test_probe_complete_shed_reaches_valid_m0_export() -> None:
    report = probe_pipeline(_survey(), _scene(direction="rear", pitch=12.0))
    assert report["first_blocking_stage"] == "none"
    assert report["required_inputs"] == []
    assert report["m0_error"] is None


def test_probe_does_not_convert_shed_to_false_gable_or_flat() -> None:
    scene = _scene(direction="rear", pitch=12.0)
    report = probe_pipeline(_survey(), scene)
    assert scene.roofs[0].type.value == "shed"
    assert report["first_blocking_stage"] == "none"
