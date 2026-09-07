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
from brickhouse.bricks.building_layout import generate_building_brick_shell
from brickhouse.bricks.opening_representation_plan import build_opening_representation_plan
from brickhouse.geometry import generate_building_geometry


SOURCE = SourceInfo(kind=SourceKind.OBSERVED, confidence=0.9)


def _building(glazing: str) -> BuildingModel:
    return BuildingModel(
        schema_version="0.1",
        id="opening-plan-conservatism",
        name="Opening plan conservatism",
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
        openings=[Opening(
            id="ambiguous",
            type=OpeningType.UNKNOWN,
            volume_id="main",
            facade=Facade.FRONT,
            offset_horizontal=2.0,
            offset_vertical=0.0,
            width=1.6,
            height=1.5,
            source=SOURCE,
            opening_visual=OpeningVisualDescription(glazing=glazing),
        )],
        roofs=[],
        appearance=Appearance(),
        metadata=Metadata(created_from="synthetic"),
    )


def _plan(building):
    shell = generate_building_brick_shell(generate_building_geometry(building), 24)
    return build_opening_representation_plan(building, shell)


def test_plan_is_deterministic_for_identical_architectural_input():
    building = _building("clear")
    assert _plan(building).model_dump() == _plan(building).model_dump()


def test_negative_or_unknown_structured_glazing_never_enables_neutral_motif():
    for descriptor in ("unknown glazing", "non vitrée", "sans vitrage", "opaque panel"):
        reservation = _plan(_building(descriptor)).reservation("ambiguous")
        assert reservation.status == "unsupported"
        assert reservation.motif_id is None
        assert reservation.architectural_type is OpeningType.UNKNOWN
