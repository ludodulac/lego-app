from copy import deepcopy

from brickhouse.building.models import (
    Appearance,
    BuildingModel,
    Facade,
    Metadata,
    Opening,
    OpeningType,
    OpeningVisualDescription,
    Position3D,
    SourceInfo,
    SourceKind,
    Volume,
    VolumeShape,
)
from brickhouse.bricks.windows import VALIDATED_WINDOW_ASSEMBLIES
from brickhouse.pipeline import run_m0_pipeline_model, run_m0_pipeline_scene
from brickhouse.scene import ArchitecturalScene


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)
VALIDATED_GLAZING_IDS = {
    part_id
    for assembly in VALIDATED_WINDOW_ASSEMBLIES
    for part_id in (assembly.frame_part_id, assembly.pane_part_id)
}


def _opening(
    opening_id: str,
    opening_type: OpeningType,
    *,
    x: float,
    width: float,
    height: float,
    glazing: str | None,
    leaves: int | None = None,
    panes: int | None = None,
) -> Opening:
    return Opening(
        id=opening_id,
        type=opening_type,
        volume_id="main",
        facade=Facade.FRONT,
        offset_horizontal=x,
        offset_vertical=1.0 if opening_type is OpeningType.WINDOW else 0.0,
        width=width,
        height=height,
        source=SOURCE,
        opening_visual=OpeningVisualDescription(
            glazing=glazing,
            leaf_count=leaves,
            pane_count=panes,
        ),
    )


def _building(openings: list[Opening]) -> BuildingModel:
    return BuildingModel(
        schema_version="0.1",
        id="bh176-generic",
        name="Opening plan pipeline fixture",
        building_type="building",
        units="m",
        volumes=[Volume(
            id="main",
            shape=VolumeShape.RECTANGULAR_PRISM,
            position=Position3D(x=0, y=0, z=0),
            width=10,
            depth=7,
            height=6,
            floors=2,
            source=SOURCE,
        )],
        openings=openings,
        roofs=[],
        appearance=Appearance(),
        metadata=Metadata(created_from="synthetic"),
    )


def test_m0_pipeline_emits_real_planned_parts_with_opening_provenance_and_preserves_semantics():
    building = _building([
        _opening("window", OpeningType.WINDOW, x=0.8, width=0.8, height=1.2, glazing="clear", leaves=1, panes=1),
        _opening("door", OpeningType.DOOR, x=3.0, width=1.6, height=2.0, glazing="clear", leaves=2, panes=2),
        _opening("unknown", OpeningType.UNKNOWN, x=6.5, width=1.6, height=1.5, glazing="clear"),
    ])
    before = deepcopy(building.model_dump())

    bundle = run_m0_pipeline_model(building, front_width_studs=24)

    assert building.model_dump() == before
    assert [opening.type for opening in building.openings] == [
        OpeningType.WINDOW,
        OpeningType.DOOR,
        OpeningType.UNKNOWN,
    ]
    for opening_id in {"window", "door", "unknown"}:
        parts = [part for part in bundle.brick_model.parts if part.opening_id == opening_id]
        assert parts
        assert {part.part_id for part in parts}.issubset(VALIDATED_GLAZING_IDS)
        assert all(part.part_id != "BRICK_1X1" for part in parts)


def test_unsupported_known_window_stays_void_and_is_reported_as_blocker_without_fake_joinery():
    building = _building([
        _opening(
            "unsupported-window",
            OpeningType.WINDOW,
            x=2.0,
            width=1.6,
            height=1.5,
            glazing="clear",
            leaves=3,
            panes=7,
        )
    ])

    bundle = run_m0_pipeline_model(building, front_width_studs=24)

    assert not [part for part in bundle.brick_model.parts if part.opening_id == "unsupported-window"]
    issues = [issue for issue in bundle.fidelity_issues if issue.object_id == "unsupported-window"]
    assert any(issue.code == "lego_architectural_window_unrepresented" and issue.severity == "blocker" for issue in issues)


def test_scene_structured_unknown_glazing_uses_planned_assembly_not_legacy_brick_cells():
    scene = ArchitecturalScene.model_validate({
        "schema_version": "0.2",
        "id": "bh176-scene",
        "name": "Scene opening plan fixture",
        "units": "m",
        "volumes": [{
            "id": "main",
            "position": {"x": 0, "y": 0, "z": 0},
            "width": {"value": 10, "source": {"kind": "observed", "confidence": 0.9}},
            "depth": {"value": 7, "source": {"kind": "observed", "confidence": 0.9}},
            "height": {"value": 6, "source": {"kind": "observed", "confidence": 0.9}},
            "floors": 2,
            "source": {"kind": "observed", "confidence": 0.9},
        }],
        "openings": [{
            "id": "unknown-glazed",
            "type": "unknown",
            "volume_id": "main",
            "facade": "front",
            "offset_horizontal": 3.0,
            "offset_vertical": 0.0,
            "width": 1.6,
            "height": 1.5,
            "source": {"kind": "observed", "confidence": 0.9},
            "opening_visual": {"glazing": "clear"},
            "evidence": [{"photo_index": 1, "observation": "Observed glazed opening; subtype unresolved."}],
        }],
        "appearance": {},
    })
    before = deepcopy(scene.model_dump())

    bundle = run_m0_pipeline_scene(scene, front_width_studs=24)

    assert scene.model_dump() == before
    assert scene.openings[0].type is OpeningType.UNKNOWN
    parts = [part for part in bundle.brick_model.parts if part.opening_id == "unknown-glazed"]
    assert parts
    assert {part.part_id for part in parts}.issubset(VALIDATED_GLAZING_IDS)
    assert all(not part.placement_id.startswith("scene-glazing:") for part in parts)
    assert all(part.part_id != "BRICK_1X1" for part in parts)


def test_structured_glass_blocks_do_not_get_reclassified_as_framed_window_motif():
    building = _building([
        _opening(
            "glass-blocks",
            OpeningType.UNKNOWN,
            x=2.0,
            width=1.6,
            height=1.5,
            glazing="glass blocks",
        )
    ])

    bundle = run_m0_pipeline_model(building, front_width_studs=24)

    assert not [part for part in bundle.brick_model.parts if part.opening_id == "glass-blocks"]
    assert not any(
        issue.object_id == "glass-blocks" and issue.severity == "blocker"
        for issue in bundle.fidelity_issues
    )
