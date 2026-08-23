from types import SimpleNamespace

from brickhouse.building.models import SourceInfo
from brickhouse.pipeline import _source_confidence_issue


def _obj(object_id: str, confidence: float, kind: str = "inferred"):
    return SimpleNamespace(
        id=object_id,
        source=SourceInfo(kind=kind, confidence=confidence),
    )


def test_low_confidence_exterior_geometry_is_visible_in_final_audit() -> None:
    warning = _source_confidence_issue("StairRun", _obj("stair-ambiguous", 0.45))
    assert warning is not None
    assert warning.code == "low_confidence_exterior_geometry"
    assert warning.severity == "warning"
    assert warning.object_id == "stair-ambiguous"

    info = _source_confidence_issue("Platform", _obj("landing-estimated", 0.58))
    assert info is not None
    assert info.severity == "info"


def test_confident_or_user_measured_exterior_geometry_does_not_emit_noise() -> None:
    assert _source_confidence_issue("Platform", _obj("deck-good", 0.82)) is None
    assert _source_confidence_issue("Platform", _obj("deck-measured", 1.0, kind="user_provided")) is None
