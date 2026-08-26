from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.scene import ArchitecturalScene


def _source(kind="user_provided", confidence=1.0):
    return {"kind": kind, "confidence": confidence}


def _scene_with_unresolved_secondary():
    return ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "partial-depth-house",
        "name": "Partial depth house",
        "units": "m",
        "volumes": [
            {
                "id": "main",
                "position": {"x": 0, "y": 0, "z": 0},
                "width": {"value": 10.0, "source": _source(), "evidence": []},
                "depth": {"value": 8.0, "source": _source(), "evidence": []},
                "height": {"value": 3.0, "source": _source(), "evidence": []},
                "floors": 1,
                "source": _source(),
                "evidence": [],
            },
            {
                "id": "unknown-wing",
                "position": {"x": 10, "y": 0, "z": 0},
                "width": {"value": None, "source": _source("inferred", 0.3), "evidence": []},
                "depth": {"value": None, "source": _source("inferred", 0.3), "evidence": []},
                "height": {"value": None, "source": _source("inferred", 0.3), "evidence": []},
                "floors": 1,
                "source": _source("inferred", 0.3),
                "evidence": [],
            },
        ],
        "openings": [{
            "id": "front-window",
            "type": "window",
            "volume_id": "main",
            "facade": "front",
            "offset_horizontal": 4.0,
            "offset_vertical": 0.8,
            "width": 2.0,
            "height": 1.4,
            "source": _source(),
            "evidence": [],
        }],
        "roofs": [],
        "appearance": {},
        "wall_profile_observations": [{
            "id": "front-depth",
            "volume_id": "main",
            "facade": "front",
            "openings_recessed": True,
            "wall_thickness": {"value": 1.0, "source": _source(), "evidence": []},
            "reveal_depth": {"value": 0.5, "source": _source(), "evidence": []},
            "source": _source(),
            "evidence": [],
        }],
    })


def test_partial_build_applies_primary_wall_depth_while_omitting_unresolved_volume():
    bundle = run_partial_scene_pipeline(
        _scene_with_unresolved_secondary(),
        front_width_studs=20,
    )

    assert bundle.brick_model.volume_id == "main"
    depth_parts = [
        part for part in bundle.brick_model.parts
        if part.placement_id.startswith("wall-depth:front-depth:1:")
    ]
    assert depth_parts
    assert {part.y_studs for part in depth_parts} == {1}

    panes = [
        part for part in bundle.brick_model.parts
        if part.facade.value == "front" and part.category == "window_pane"
    ]
    assert panes
    assert {part.y_studs for part in panes} == {1}

    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan is not None
    assert bundle.assembly_plan.total_parts == len(bundle.brick_model.parts)
    assert any(
        issue.code == "partial_preview_secondary_volume_omitted"
        and issue.object_id == "unknown-wing"
        for issue in bundle.fidelity_issues
    )
