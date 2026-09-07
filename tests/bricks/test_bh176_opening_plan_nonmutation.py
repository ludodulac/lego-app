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
from brickhouse.pipeline import run_m0_pipeline_model


def test_pipeline_does_not_mutate_architectural_opening_truth():
    source = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)
    building = BuildingModel(
        schema_version="0.1",
        id="bh176-nonmutation",
        name="Nonmutation fixture",
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
            id="semantic-unknown",
            type=OpeningType.UNKNOWN,
            volume_id="main",
            facade=Facade.FRONT,
            offset_horizontal=3.0,
            offset_vertical=0.0,
            width=1.6,
            height=1.5,
            source=source,
            opening_visual=OpeningVisualDescription(glazing="clear"),
        )],
        roofs=[],
        appearance=Appearance(),
        metadata=Metadata(created_from="synthetic"),
    )
    before = deepcopy(building.model_dump())

    run_m0_pipeline_model(building, front_width_studs=24)

    assert building.model_dump() == before
    assert building.openings[0].type is OpeningType.UNKNOWN
