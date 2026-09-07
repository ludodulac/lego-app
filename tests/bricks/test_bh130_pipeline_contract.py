from brickhouse.building.models import (
    Appearance,
    BuildingModel,
    Facade,
    Metadata,
    Opening,
    OpeningType,
    Position3D,
    SourceInfo,
    SourceKind,
    Volume,
    VolumeShape,
)
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.export import BrickExportFidelityIssue
from brickhouse.geometry import generate_building_geometry
import brickhouse.pipeline as pipeline


def test_pipeline_runs_facade_rhythm_fidelity_on_the_applied_opening_plan(monkeypatch):
    source = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)
    building = BuildingModel(
        schema_version="0.1",
        id="bh130-behavioral",
        name="Facade rhythm wiring fixture",
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
            source=source,
        )],
        openings=[Opening(
            id="window",
            type=OpeningType.WINDOW,
            volume_id="main",
            facade=Facade.FRONT,
            offset_horizontal=2.0,
            offset_vertical=1.0,
            width=1.0,
            height=1.2,
            source=source,
        )],
        roofs=[],
        appearance=Appearance(),
        metadata=Metadata(created_from="synthetic"),
    )
    shell = generate_building_brick_shell(generate_building_geometry(building), 24)
    seen = []
    sentinel = BrickExportFidelityIssue(
        code="bh130_facade_rhythm_called",
        severity="info",
        message="behavioral wiring sentinel",
    )

    def fake_facade_rhythm(application):
        seen.append(application)
        return [sentinel]

    monkeypatch.setattr(pipeline, "facade_rhythm_fidelity_issues", fake_facade_rhythm)

    prepared_shell, plan, issues = pipeline._prepare_opening_shell(building, shell)

    assert len(seen) == 1
    assert seen[0].shell == prepared_shell
    assert plan.building_id == building.id
    assert sentinel in issues
