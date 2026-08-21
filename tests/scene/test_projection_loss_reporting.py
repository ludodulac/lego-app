from brickhouse.scene import ArchitecturalScene, project_scene_to_building


def test_projection_reports_scene_information_that_m0_drops() -> None:
    scene = ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "losses",
        "name": "Projection losses",
        "units": "m",
        "volumes": [{"id": "v", "position": {"x": 0, "y": 0, "z": 0}, "width": {"value": 10, "source": {"kind": "user_provided", "confidence": 1}}, "depth": {"value": 8, "source": {"kind": "inferred", "confidence": 0.6}}, "height": {"value": 6, "source": {"kind": "inferred", "confidence": 0.6}}, "floors": 2, "source": {"kind": "inferred", "confidence": 0.6}}],
        "openings": [{"id": "w", "type": "window", "volume_id": "v", "facade": "right", "offset_horizontal": 4, "offset_vertical": 0.5, "width": 1, "height": 1, "source": {"kind": "inferred", "confidence": 0.6}, "local_grade_clearance": 0.1, "window_style": "simple", "has_sill": False, "has_decorative_surround": False}],
        "roofs": [{"id": "r", "volume_id": "v", "type": "gable", "overhang": 0.3, "ridge_direction": "depth", "pitch_degrees": 20, "source": {"kind": "inferred", "confidence": 0.5}}],
        "terrain": {"kind": "facade_grade_profiles", "profiles": [{"facade": "right", "start_elevation": 0, "end_elevation": 1.5, "source": {"kind": "inferred", "confidence": 0.5}}]},
        "equipment": [{"id": "down", "type": "downspout", "facade": "right", "source": {"kind": "observed", "confidence": 0.8}}],
        "visibility": [{"facade": "right", "spans": [{"from": 0, "to": 8, "state": "visible"}]}],
        "appearance": {"walls": {"color": "off_white"}, "roof": {"color": "dark_gray"}, "frames": {"color": "dark_brown"}},
    })
    result = project_scene_to_building(scene)
    codes = {issue.code for issue in result.issues}
    assert {"terrain_not_supported", "equipment_not_supported", "visibility_not_supported", "local_grade_clearance_not_supported"} <= codes
