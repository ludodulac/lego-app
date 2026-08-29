import json
from pathlib import Path

import pytest

from brickhouse.scene_cli import apply_opening_visual_evidence, load_architectural_scene, write_scene_export


SCENE = Path("tests/fixtures/brickhouse_scene_current.json")
EVIDENCE = Path("tests/fixtures/real_house_5_shutter_observations.json")


def test_opening_visual_evidence_updates_only_explicit_visual_fields() -> None:
    scene = load_architectural_scene(SCENE)
    before = {opening.id: opening for opening in scene.openings}

    overlaid = apply_opening_visual_evidence(scene, EVIDENCE)
    after = {opening.id: opening for opening in overlaid.openings}

    confirmed = {
        "front_window_upper_left",
        "front_window_upper_right",
        "front_window_middle_right",
        "right_window_upper",
    }
    assert set(after) == set(before)

    for opening_id in confirmed:
        visual = after[opening_id].opening_visual
        assert visual is not None
        assert visual.shutter_count == 2
        assert visual.shutter_style == "folding"
        assert visual.shutter_state == "open_folded_at_sides"
        assert visual.shutter_color == "white"

    assert after["front_window_middle_left"].opening_visual == before["front_window_middle_left"].opening_visual

    for opening_id in set(after) - confirmed:
        if opening_id == "front_window_middle_left":
            continue
        assert after[opening_id].model_dump(exclude={"opening_visual"}) == before[opening_id].model_dump(exclude={"opening_visual"})


def test_opening_visual_evidence_preserves_existing_visual_fields(tmp_path: Path) -> None:
    scene = load_architectural_scene(SCENE)
    target = next(opening for opening in scene.openings if opening.id == "front_window_upper_left")
    existing = target.opening_visual.model_dump(exclude_none=True) if target.opening_visual else {}
    existing["frame_color"] = "cream"
    replacement = target.model_copy(update={"opening_visual": target.opening_visual.model_validate(existing) if target.opening_visual else None})
    if replacement.opening_visual is None:
        from brickhouse.building.models import OpeningVisualDescription
        replacement = target.model_copy(update={"opening_visual": OpeningVisualDescription(frame_color="cream")})
    scene = scene.model_copy(update={
        "openings": [replacement if opening.id == target.id else opening for opening in scene.openings]
    })

    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps({"observations": [{"opening_id": target.id, "shutter_count": 2}]}), encoding="utf-8")

    overlaid = apply_opening_visual_evidence(scene, evidence)
    visual = next(opening.opening_visual for opening in overlaid.openings if opening.id == target.id)
    assert visual is not None
    assert visual.frame_color == "cream"
    assert visual.shutter_count == 2


def test_opening_visual_evidence_rejects_unknown_opening_id(tmp_path: Path) -> None:
    scene = load_architectural_scene(SCENE)
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps({"observations": [{"opening_id": "missing-opening", "shutter_count": 2}]}), encoding="utf-8")

    with pytest.raises(ValueError, match="unknown opening id 'missing-opening'"):
        apply_opening_visual_evidence(scene, evidence)


def test_partial_scene_export_consumes_confirmed_shutter_overlay(tmp_path: Path) -> None:
    bundle = write_scene_export(
        SCENE,
        tmp_path / "partial.json",
        front_width_studs=48,
        allow_partial=True,
        opening_visual_evidence=EVIDENCE,
    )
    rendered_ids = {
        part.opening_id
        for part in bundle.brick_model.parts
        if part.placement_id.startswith("scene-shutter:")
    }
    assert rendered_ids == {
        "front_window_upper_left",
        "front_window_upper_right",
        "front_window_middle_right",
        "right_window_upper",
    }
    assert "front_window_middle_left" not in rendered_ids
    assert bundle.bom.total_parts == len(bundle.brick_model.parts)
    assert bundle.assembly_plan is not None
    assert bundle.assembly_plan.total_parts == len(bundle.brick_model.parts)
    assert bundle.instruction_plan is not None
    assert bundle.instruction_plan.total_parts == len(bundle.brick_model.parts)
    assert [pid for step in bundle.instruction_plan.steps for pid in step.placement_ids] == [
        pid for step in bundle.assembly_plan.steps for pid in step.placement_ids
    ]
    assert bundle.bag_plan is not None
    assert bundle.bag_plan.total_parts == len(bundle.brick_model.parts)
    assert [pid for bag in bundle.bag_plan.bags for pid in bag.placement_ids] == [
        pid for step in bundle.assembly_plan.steps for pid in step.placement_ids
    ]
