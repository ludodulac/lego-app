from brickhouse.bricks.windows import WindowPartPlacement, WindowRepresentationStatus
from brickhouse.building.models import Facade
from brickhouse.pipeline import _window_representation_issues


def test_unrepresented_architectural_window_has_explicit_void_only_status():
    status = WindowRepresentationStatus(
        opening_id="generic-window",
        facade=Facade.FRONT,
        represented=False,
        representation="void_only",
    )
    assert status.opening_id == "generic-window"
    assert not status.represented
    assert status.representation == "void_only"


def test_unrepresented_architectural_window_becomes_export_blocker():
    issues = _window_representation_issues([
        WindowRepresentationStatus(
            opening_id="generic-window",
            facade=Facade.FRONT,
            represented=False,
            representation="void_only",
        )
    ])
    assert len(issues) == 1
    assert issues[0].code == "lego_architectural_window_unrepresented"
    assert issues[0].severity == "blocker"
    assert issues[0].object_id == "generic-window"


def test_represented_architectural_window_does_not_create_blocker():
    issues = _window_representation_issues([
        WindowRepresentationStatus(
            opening_id="generic-window",
            facade=Facade.FRONT,
            represented=True,
            representation="validated_assembly",
        )
    ])
    assert issues == []


def test_window_part_can_carry_architectural_opening_provenance():
    part = WindowPartPlacement(
        part_id="WINDOW_1X2X2_60592",
        category="window_frame",
        facade=Facade.FRONT,
        x_studs=2,
        y_studs=0,
        z_plates=6,
        rotation_quarter_turns=1,
        opening_id="generic-window",
    )
    assert part.opening_id == "generic-window"
