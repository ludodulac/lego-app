from pathlib import Path

from brickhouse.partial_scene_pipeline import _resolved_core_building, _selected_partial_volumes
from brickhouse.scene_cli import load_architectural_scene


FIXTURE = Path("tests/fixtures/brickhouse_scene_current.json")


def test_low_confidence_does_not_erase_a_resolved_secondary_volume() -> None:
    scene = load_architectural_scene(FIXTURE)

    included, omitted = _selected_partial_volumes(scene)
    building = _resolved_core_building(scene)

    assert {volume.id for volume in included} == {"volume_main", "lower_exterior_volume"}
    assert not omitted
    assert {volume.id for volume in building.volumes} == {"volume_main", "lower_exterior_volume"}


def test_unresolved_secondary_volume_is_still_omitted() -> None:
    scene = load_architectural_scene(FIXTURE)
    secondary = scene.volumes[1]
    unresolved = secondary.model_copy(update={
        "depth": secondary.depth.model_copy(update={"value": None})
    })
    candidate = scene.model_copy(update={"volumes": [scene.volumes[0], unresolved]})

    included, omitted = _selected_partial_volumes(candidate)

    assert [volume.id for volume in included] == ["volume_main"]
    assert [(volume.id, reason) for volume, reason in omitted] == [
        ("lower_exterior_volume", "unresolved metric envelope")
    ]
