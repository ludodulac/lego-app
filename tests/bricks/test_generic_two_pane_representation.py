import json
from pathlib import Path

from brickhouse.bricks import (
    apply_opening_representation_plan,
    build_opening_representation_plan,
    generate_building_brick_shell,
    generate_planned_opening_parts,
)
from brickhouse.geometry import generate_building_geometry
from brickhouse.scene import ArchitecturalScene, project_scene_to_building


FIXTURE = Path(__file__).parents[1] / "fixtures" / "generic_opening_pane_count_fidelity.json"


def _building_with_pane_count(pane_count):
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))["scene"]
    scene = ArchitecturalScene.model_validate(payload)
    openings = []
    for opening in scene.openings:
        if opening.id != "window_two_visible_panes":
            openings.append(opening)
            continue
        visual = opening.opening_visual
        openings.append(opening.model_copy(update={
            "opening_visual": visual.model_copy(update={"pane_count": pane_count})
        }))
    scene = scene.model_copy(update={"openings": openings})
    projection = project_scene_to_building(scene)
    assert projection.building is not None
    return projection.building


def _plan_and_parts(building):
    shell = generate_building_brick_shell(generate_building_geometry(building), 48)
    plan = build_opening_representation_plan(building, shell)
    application = apply_opening_representation_plan(building, shell, plan)
    parts, represented, statuses = generate_planned_opening_parts(building, application.shell, plan)
    return shell, plan, parts, represented, {item.opening_id: item for item in statuses}


def test_unknown_topology_keeps_historical_fallback_unchanged():
    building = _building_with_pane_count(None)
    _, plan, parts, represented, statuses = _plan_and_parts(building)
    reservation = plan.reservation("window_two_visible_panes")
    assert reservation is not None
    assert reservation.status == "unsupported"
    assert statuses["window_two_visible_panes"].representation == "legacy_window_fallback"
    assert "window_two_visible_panes" in represented
    assert parts


def test_known_two_panes_use_raster_preserving_generic_split_without_semantic_strengthening():
    building = _building_with_pane_count(2)
    shell, plan, parts, represented, statuses = _plan_and_parts(building)
    opening = next(item for item in building.openings if item.id == "window_two_visible_panes")
    reservation = plan.reservation(opening.id)
    wall = next(item for item in shell.walls if item.facade.value == "front")
    raster = next(item for item in wall.grid.openings if item.id == opening.id)

    assert opening.opening_visual.pane_count == 2
    assert opening.opening_visual.leaf_count is None
    assert opening.window_style is None
    assert reservation is not None
    assert reservation.status == "reserved"
    assert reservation.motif_id == "generic_two_pane:raster_split"
    assert reservation.width_studs == raster.width_studs
    assert reservation.height_bricks == raster.height_bricks
    assert statuses[opening.id].representation == "generic_two_pane"
    assert opening.id in represented

    opening_parts = [part for part in parts if part.opening_id == opening.id]
    assert len(opening_parts) == raster.width_studs * raster.height_bricks
    frames = [part for part in opening_parts if part.category == "window_frame"]
    panes = [part for part in opening_parts if part.category == "window_pane"]
    assert len(frames) == raster.height_bricks
    assert len(panes) == (raster.width_studs - 1) * raster.height_bricks
