import json
from pathlib import Path

from brickhouse.scene import ArchitecturalScene
from brickhouse.scene.benchmark_scene_recipe import materialize_scene_recipe


ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_FIXTURE = ROOT / "tests" / "fixtures" / "architectural_scene_partial_wall.json"
REAL_HOUSE_RECIPE = ROOT / "frontend" / "benchmarks" / "real-house-5" / "scene-candidate-v0.2.json"
VIEWER = ROOT / "frontend" / "scene-viewer.js"


def test_partial_wall_fixture_validates_and_roundtrips_without_creating_enclosure():
    raw = json.loads(SYNTHETIC_FIXTURE.read_text(encoding="utf-8"))
    scene = ArchitecturalScene.model_validate(raw)

    assert [volume.id for volume in scene.volumes] == ["volume_main"]
    assert [platform.id for platform in scene.platforms] == ["landing-1"]
    assert [wall.id for wall in scene.partial_wall_segments] == ["partial-wall-1"]
    assert scene.partial_wall_segments[0].thickness is None

    serialized = scene.model_dump(mode="json", by_alias=True)
    restored = ArchitecturalScene.model_validate(serialized)
    assert restored == scene
    assert len(serialized["volumes"]) == 1
    assert serialized["partial_wall_segments"][0]["thickness"] is None


def test_scene_viewer_renders_partial_wall_as_plane_not_box():
    source = VIEWER.read_text(encoding="utf-8")
    start = source.index("function renderPartialWallSegments()")
    end = source.index("function renderStairs()", start)
    renderer = source[start:end]

    assert "currentScene.partial_wall_segments" in renderer
    assert "THREE.BufferGeometry" in renderer
    assert "THREE.DoubleSide" in renderer
    assert "THREE.BoxGeometry" not in renderer
    assert "zero-thickness visible plane when architectural thickness is unknown" in renderer
    assert "renderPartialWallSegments();" in source


def test_real_house_recipe_adds_only_observed_partial_masonry_wall_and_keeps_void_open():
    scene = materialize_scene_recipe(REAL_HOUSE_RECIPE)

    assert [volume.id for volume in scene.volumes] == ["volume_main"]
    assert all(volume.id != "volume-exterior-1" for volume in scene.volumes)
    assert [wall.id for wall in scene.partial_wall_segments] == ["covered-void-right-masonry-wall-1"]

    wall = scene.partial_wall_segments[0]
    assert wall.material.value == "masonry"
    assert wall.thickness is None
    assert wall.height.value == 2.3
    assert {item.photo_index for item in wall.evidence} == {4, 5}

    # This first slice deliberately keeps the covered region open: it adds one
    # bounded wall plane, not a new room, volume, rear wall or lateral closure.
    assert len(scene.partial_wall_segments) == 1
    assert {platform.id for platform in scene.platforms} >= {"platform-massive-1", "platform-timber-1"}
    assert {stair.id for stair in scene.stairs} == {
        "stair-exterior-1-run-lower-v1",
        "stair-exterior-1-run-upper-v1",
    }
